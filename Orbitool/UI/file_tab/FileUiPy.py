from functools import partial
from stat import FILE_ATTRIBUTE_SPARSE_FILE
from typing import DefaultDict, Dict, Iterable, List, Optional, Union, cast
from collections import Counter

from PyQt6 import QtCore, QtGui, QtWidgets

from Orbitool import utils
from Orbitool.UI.utils.utils import TableUtils
from Orbitool.models.file import (FileSpectrumInfo, Path, PathList)
from Orbitool.utils.readers import SpectrumFilter

from .. import utils as UiUtils
from ..manager import Manager, Thread, state_node
from ..utils import DragHelper, set_header_sizes, showInfo
from . import FileUi
from .utils import str2timedelta


class Widget(QtWidgets.QWidget):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.manager: Manager = manager
        self.ui = FileUi.Ui_Form()
        self.drag_helper = DragHelper(("file",))
        self.setupUi()

        manager.init_or_restored.connect(self.init_or_restore)
        manager.save.connect(self.updateState)
        self.current_edit_filter = None
        self.current_filter_combobox: Union[QtWidgets.QComboBox, None] = None

    def setupUi(self):
        self.ui.setupUi(self)

        ui = self.ui

        ui.tableWidget.itemDoubleClicked.connect(self.showFileDetail)
        ui.tableWidget.dragEnterEvent = self.tableDragEnterEvent
        ui.tableWidget.dragMoveEvent = self.tableDragMoveEvent
        ui.tableWidget.dropEvent = self.tableDropEvent

        ui.addFilePushButton.clicked.connect(self.addThermoFile)
        ui.addFolderPushButton.clicked.connect(self.addFolder)
        ui.removeFilePushButton.clicked.connect(self.removePath)

        ui.timeAdjustPushButton.clicked.connect(self.adjust_time)
        ui.refreshFilterPushButton.clicked.connect(self.refreshFilter)

        ui.periodToolButton.clicked.connect(self.edit_period)

        ui.filterTableWidget.itemDoubleClicked.connect(self.editFilter)
        ui.addFilterToolButton.clicked.connect(self.addFilter)
        ui.delFilterToolButton.clicked.connect(self.delFilter)

        ui.selectedPushButton.clicked.connect(self.processSelected)
        ui.allPushButton.clicked.connect(self.processAll)

    @property
    def info(self):
        return self.manager.workspace.info.file_tab

    @property
    def pathlist(self) -> PathList:
        return self.info.pathlist

    def init_or_restore(self):
        self.showPaths()
        self.info.ui_state.restore_state(self.ui)

    def updateState(self):
        ui = self.ui
        self.info.ui_state.store_state(ui)

    @state_node
    def edit_period(self):
        from .CustomPeriodUiPy import Dialog
        ui = self.ui
        start_time = ui.startDateTimeEdit.dateTime().toPyDateTime()
        end_time = ui.endDateTimeEdit.dateTime().toPyDateTime()
        time_interval = ui.nMinutesLineEdit.text()
        dialog = Dialog(
            self.manager, start_time, end_time,
            ui.nSpectraSpinBox.value(), time_interval)
        dialog.init_periods(start_time, end_time, time_interval)
        dialog.show_periods()
        dialog.exec()

    @state_node
    def addThermoFile(self):
        files = UiUtils.openfiles(
            "Select one or more files", "RAW files(*.RAW)")
        pathlist = self.pathlist

        info = self.info

        def func():
            for f in files:
                path = pathlist.addThermoFile(f)
                for filter in path.getFileHandler().getUniqueFilters():
                    info.addFilter(filter)

            pathlist.sort()
            self.refreshFilterPolarity()
            return len(pathlist.paths)

        length = yield func, "read files"

        self.showPaths()
        self.showFilter()

    @addThermoFile.except_node
    def addThermoFile(self):
        self.showPaths()

    @state_node
    def addFolder(self):
        ret, folder = UiUtils.openfolder("Select one folder")
        if not ret:
            return
        pathlist = self.pathlist
        info = self.info

        manager = self.manager

        def func():
            for path in manager.tqdm(utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.ui.recursionCheckBox.isChecked())):
                p = pathlist.addThermoFile(path)
                for filter in p.getFileHandler().getUniqueFilters():
                    info.addFilter(filter)
            pathlist.sort()
            self.refreshFilterPolarity()

        yield func, "read folders"

        self.showPaths()
        self.showFilter()

    @addFolder.except_node
    def addFolder(self):
        self.showPaths()
        self.showFilter()

    @state_node(withArgs=True)
    def showFileDetail(self, item: QtWidgets.QTableWidgetItem):
        from .FileDetailUiPy import Dialog
        Dialog(self.manager, item.row()).exec()

    def tableDragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if self.drag_helper.accept(event.mimeData()):
            event.setDropAction(QtCore.Qt.DropAction.LinkAction)
            event.accept()

    def tableDragMoveEvent(self, event: QtGui.QDragMoveEvent):
        event.accept()

    @state_node(withArgs=True)
    def tableDropEvent(self, event: QtGui.QDropEvent):
        data = event.mimeData()
        paths = list(self.drag_helper.yield_file(data))
        info = self.info

        def func():
            pathlist = self.pathlist
            for p in paths:
                if p.is_dir():
                    for path in self.manager.tqdm(utils.files.FolderTraveler(str(p), ext=".RAW", recurrent=self.ui.recursionCheckBox.isChecked())):
                        for filter in pathlist.addThermoFile(path).getFileHandler().getUniqueFilters():
                            info.addFilter(filter)
                elif p.suffix.lower() == ".raw":
                    for filter in pathlist.addThermoFile(str(p)).getFileHandler().getUniqueFilters():
                        info.addFilter(filter)
            pathlist.sort()
            self.refreshFilterPolarity()
        yield func, "read files"

        self.showPaths()
        self.showFilter()

    @state_node
    def removePath(self):
        indexes = TableUtils.getSelectedRow(self.ui.tableWidget)
        paths = self.pathlist.rmPath(indexes)
        info = self.info

        def func():
            for path in paths:
                for f in path.getFileHandler().getUniqueFilters():
                    info.rmFilter(f)
        yield func

        self.showPaths()
        self.showFilter()

    @removePath.except_node
    def removePath(self):
        self.showPaths()
        self.showFilter()

    def showPaths(self):
        ui = self.ui
        table = ui.tableWidget
        pathlist = self.pathlist
        table.setRowCount(0)
        table.setRowCount(len(pathlist))

        for i, f in enumerate(pathlist):
            v = [f.get_show_name(), f.startDatetime.replace(microsecond=0),
                 f.endDatetime.replace(microsecond=0), f.scanNum, f.path]
            for j, vv in enumerate(v):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(vv)))
        table.resizeColumnsToContents()
        table.setColumnWidth(0, 150)

        if ui.autoTimeCheckBox.isChecked():
            time_start, time_end = pathlist.timeRange
            if time_start is None:
                return
            ui.startDateTimeEdit.setDateTime(time_start)
            ui.endDateTimeEdit.setDateTime(time_end)

    @state_node
    def adjust_time(self):
        ui = self.ui
        slt = TableUtils.getSelectedRow(ui.tableWidget)
        paths = self.pathlist.subList(slt)
        start, end = paths.timeRange
        if start is None:
            return
        ui.startDateTimeEdit.setDateTime(start)
        ui.endDateTimeEdit.setDateTime(end)

    @state_node
    def refreshFilter(self):
        ui = self.ui
        info = self.info
        file_filters = info.getCastedFilesSpectrumFilters()
        file_filters.clear()
        for path in info.pathlist:
            for filter in path.getFileHandler().getUniqueFilters():
                info.addFilter(filter)
        self.showFilter()

    def refreshFilterPolarity(self):
        file_filters = self.info.getCastedFilesSpectrumFilters()
        used_filters = self.info.getCastedUsedSpectrumFilters()
        key = "polarity"
        if key not in used_filters and file_filters.get(key, False):
            used_filters[key] = file_filters[key].most_common(1)[0][0]

    def showFilter(self):
        table = self.ui.filterTableWidget
        use_filter = self.info.getCastedUsedSpectrumFilters()
        scanstats_filter = self.info.getCastedScanstatsFilters()
        self.current_filter_combobox = None
        self.current_edit_filter = None
        TableUtils.clearAndSetRowCount(table, len(
            use_filter) + sum(map(len, scanstats_filter.values())))

        for row, (name, value) in enumerate(use_filter.items()):
            TableUtils.setRow(
                table, row,
                name,
                "==",
                value)

        row = len(use_filter)
        for name, ops in scanstats_filter.items():
            for op, value in ops.items():
                row += 1
                TableUtils.setRow(
                    table, row,
                    name,
                    op,
                    value)
        table.resizeColumnsToContents()

    @state_node(withArgs=True, mode="e")
    def editFilter(self, item: QtWidgets.QTableWidgetItem):
        table = self.ui.filterTableWidget
        file_filter = self.info.getCastedFilesSpectrumFilters()
        use_filter = self.info.getCastedUsedSpectrumFilters()
        row = item.row()
        col = item.column()

        key = table.item(row, 0).text()
        op = table.item(row, 1).text()
        value = table.item(row, 2).text()

        previous = item.text()

        combobox = QtWidgets.QComboBox()

        def textChanged(e):
            cur_key = key
            cur_op = op
            cur_value = value
            self.current_edit_filter = None
            print(f"delete {row} {col}")
            table.removeCellWidget(row, col)
            self.current_filter_combobox = None
            if previous != combobox.currentText():
                current = combobox.currentText()
                match col:
                    case 0:
                        del use_filter[key]
                        cur_key = current
                        cur_value = use_filter[cur_key] = file_filter[cur_key].most_common(1)[
                            0][0]
                    case 1:
                        pass
                    case 2:
                        cur_value = use_filter[cur_key] = current
            TableUtils.setRow(
                table, row,
                cur_key,
                cur_op,
                cur_value
            )
            table.resizeColumnsToContents()
        if self.current_edit_filter:
            self.current_filter_combobox.textActivated.emit(
                self.current_filter_combobox.currentText())
            # textActivated may delete current item
            item = table.item(row, col)
        self.current_edit_filter = (row, col)
        self.current_filter_combobox = combobox

        match col:
            case 0:
                keys = set(file_filter.keys())
                keys -= use_filter.keys()
                keys.add(previous)
                combobox.addItems(keys)
                combobox.setCurrentText(item.text())
                combobox.textActivated.connect(textChanged)
                table.setCellWidget(item.row(), 0, combobox)
            case 1:
                combobox.addItem("==")
                combobox.setCurrentText(item.text())
                combobox.textActivated.connect(textChanged)
                table.setCellWidget(item.row(), 1, combobox)
            case 2:
                combobox.addItems(file_filter[key].keys())
                combobox.setCurrentText(item.text())
                combobox.textActivated.connect(textChanged)
                table.setCellWidget(item.row(), 2, combobox)
        table.resizeColumnsToContents()
        combobox.setFocus()
        combobox.showPopup()

    @state_node
    def addFilter(self):
        file_filter = self.info.getCastedFilesSpectrumFilters()
        use_filter = self.info.getCastedUsedSpectrumFilters()
        if len(file_filter) == len(use_filter):
            self.manager.msg.emit("All filter are added")
            return
        
        for key in file_filter.keys():
            if key not in use_filter:
                use_filter[key] = file_filter[key].most_common(1)[0][0]
                break
        
        self.showFilter()

    @state_node
    def delFilter(self):
        table = self.ui.filterTableWidget
        slt = TableUtils.getSelectedRow(table)
        use_filter = self.info.getCastedUsedSpectrumFilters()
        for index in slt:
            key = table.item(index, 0).text()
            use_filter.pop(key)
        
        self.showFilter()

    @state_node
    def processSelected(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.ui.tableWidget)
        if len(indexes) == 0:
            return None

        paths = self.pathlist.subList(indexes)
        self.info.spectrum_infos = yield self.processPaths(paths.paths), "get infomations from selected spectra"

        self.callback.emit()

    @state_node
    def processAll(self):
        self.info.spectrum_infos = yield self.processPaths(self.pathlist.paths), "get infomations from spectra"

        self.callback.emit()

    def processPaths(self, paths: List[Path]):
        ui = self.ui
        time_range = (ui.startDateTimeEdit.dateTime().toPyDateTime(),
                      ui.endDateTimeEdit.dateTime().toPyDateTime())

        paths = self.manager.tqdm(paths)

        self.info.rtol = ui.rtolDoubleSpinBox.value() * 1e-6

        filters = self.info.getCastedUsedSpectrumFilters()
        if ui.averageGroupBox.isChecked():
            if ui.nSpectraRadioButton.isChecked():
                num = ui.nSpectraSpinBox.value()
                func = partial(FileSpectrumInfo.infosFromNumInterval,
                               paths, num, filters, time_range)
            elif ui.nMinutesRadioButton.isChecked():
                interval = str2timedelta(ui.nMinutesLineEdit.text())
                func = partial(FileSpectrumInfo.infosFromTimeInterval,
                               paths, interval, filters, time_range)
            elif ui.periodRadioButton.isChecked():
                func = partial(FileSpectrumInfo.infosFromPeriods,
                               paths, filters, self.info.periods)
        else:
            func = partial(FileSpectrumInfo.infosFromPath_withoutAveraging,
                           paths, filters, time_range)

        return func
