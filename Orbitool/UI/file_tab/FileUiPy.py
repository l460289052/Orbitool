import csv
import os
import pathlib
from datetime import datetime, timedelta
from functools import partial
from typing import Iterable, List, Optional, Union

from PyQt6 import QtCore, QtGui, QtWidgets

from ... import utils
from ...functions.file import generage_periods
from ...structures.file import FileSpectrumInfo, Path, PathList, PeriodItem
from .. import utils as UiUtils
from ..manager import Manager, Thread, state_node
from ..utils import DragHelper, set_header_sizes, showInfo
from . import FileUi
from .utils import str2timedelta


class Widget(QtWidgets.QWidget):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.ui = FileUi.Ui_Form()
        self.drag_helper = DragHelper(("file",))
        self.setupUi()

        manager.init_or_restored.connect(self.init_or_restore)
        manager.save.connect(self.updateState)

    def setupUi(self):
        self.ui.setupUi(self)

        ui = self.ui
        set_header_sizes(ui.tableWidget.horizontalHeader(), [150, 100, 100])

        ui.tableWidget.dragEnterEvent = self.tableDragEnterEvent
        ui.tableWidget.dragMoveEvent = self.tableDragMoveEvent
        ui.tableWidget.dropEvent = self.tableDropEvent

        ui.addFilePushButton.clicked.connect(self.addThermoFile)
        ui.addFolderPushButton.clicked.connect(self.addFolder)
        ui.removeFilePushButton.clicked.connect(self.removePath)

        ui.timeAdjustPushButton.clicked.connect(self.adjust_time)

        ui.periodToolButton.clicked.connect(self.edit_period)

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
        from .CustonPeriodUiPy import Dialog
        ui = self.ui
        dialog = Dialog(
            self.manager, 
            ui.startDateTimeEdit.dateTime().toPyDateTime(),
            ui.endDateTimeEdit.dateTime().toPyDateTime(),
            ui.nSpectraSpinBox.value(),
            ui.nMinutesLineEdit.text(),
            "minutes")
        dialog.exec()
        

    @state_node
    def addThermoFile(self):
        files = UiUtils.openfiles(
            "Select one or more files", "RAW files(*.RAW)")
        pathlist = self.pathlist

        def func():
            for f in files:
                pathlist.addThermoFile(f)
            pathlist.sort()
            return len(pathlist.paths)

        length = yield func, "read files"

        self.showPaths()

    @addThermoFile.except_node
    def addThermoFile(self):
        self.showPaths()

    @state_node
    def addFolder(self):
        ret, folder = UiUtils.openfolder("Select one folder")
        if not ret:
            return
        pathlist = self.pathlist

        manager = self.manager

        def func():
            for path in manager.tqdm(utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.ui.recursionCheckBox.isChecked())):
                pathlist.addThermoFile(path)
            pathlist.sort()

        yield func, "read folders"

        self.showPaths()

    @addFolder.except_node
    def addFolder(self):
        self.showPaths()

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
        def func():
            pathlist = self.pathlist
            for p in paths:
                if p.is_dir():
                    for path in self.manager.tqdm(utils.files.FolderTraveler(str(p), ext=".RAW", recurrent=self.ui.recursionCheckBox.isChecked())):
                        pathlist.addThermoFile(path)
                elif p.suffix.lower() == ".raw":
                    pathlist.addThermoFile(str(p))
            pathlist.sort()
        yield func, "read files"

        self.showPaths()

    @state_node
    def removePath(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.ui.tableWidget)
        self.pathlist.rmPath(indexes)
        self.showPaths()

    @removePath.except_node
    def removePath(self):
        self.showPaths()

    def showPaths(self):
        ui = self.ui
        table = ui.tableWidget
        pathlist = self.pathlist
        table.setRowCount(0)
        table.setRowCount(len(pathlist))

        for i, f in enumerate(pathlist):
            v = [os.path.split(f.path)[1], f.startDatetime.replace(microsecond=0),
                 f.endDatetime.replace(microsecond=0), f.path]
            for j, vv in enumerate(v):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(vv)))

        if ui.autoTimeCheckBox.isChecked():
            time_start, time_end = pathlist.timeRange
            if time_start is None:
                return
            ui.startDateTimeEdit.setDateTime(time_start)
            ui.endDateTimeEdit.setDateTime(time_end)

    @state_node
    def adjust_time(self):
        ui = self.ui
        slt = UiUtils.get_tablewidget_selected_row(ui.tableWidget)
        paths = self.pathlist.subList(slt)
        start, end = paths.timeRange
        if start is None:
            return
        ui.startDateTimeEdit.setDateTime(start)
        ui.endDateTimeEdit.setDateTime(end)

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
        if ui.positiveRadioButton.isChecked():
            polarity = 1
        elif ui.negativeRadioButton.isChecked():
            polarity = -1
        else:
            raise ValueError("Please select a polarity")

        if ui.averageCheckBox.isChecked():
            if ui.nSpectraRadioButton.isChecked():
                num = ui.nSpectraSpinBox.value()
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_number,
                               paths, num, polarity, time_range)
            elif ui.nMinutesRadioButton.isChecked():
                interval = str2timedelta(ui.nMinutesLineEdit.text())
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_time_interval,
                               paths, interval, polarity, time_range)
            elif ui.periodRadioButton.isChecked():
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_periods,
                               paths, polarity, [(p.start_time, p.end_time)for p in self.info.periods])
        else:
            func = partial(FileSpectrumInfo.generate_infos_from_paths,
                           paths, polarity, time_range)

        return func
