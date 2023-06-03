import os
import csv
from datetime import datetime, timedelta
from functools import partial
import pathlib
from typing import List, Optional, Union, Iterable

from PyQt5 import QtCore, QtWidgets, QtGui

from .. import utils
from ..structures.file import Path, PathList, FileSpectrumInfo, PeriodItem
from ..functions.file import generage_periods
from ..workspace import UiNameGetter, UiState
from . import FileUi
from . import utils as UiUtils
from .manager import Manager, Thread, state_node
from .utils import set_header_sizes, showInfo


class Widget(QtWidgets.QWidget):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.ui = FileUi.Ui_Form()
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

        ui.nSpectraRadioButton.clicked.connect(self.radioButtonChanged)
        ui.nMinutesRadioButton.clicked.connect(self.radioButtonChanged)
        ui.periodRadioButton.clicked.connect(self.radioButtonChanged)

        ui.periodImportToolButton.clicked.connect(self.importPeriod)
        ui.exportPeriodPushButton.clicked.connect(self.exportPeriod)

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

    @state_node(mode='n')
    def radioButtonChanged(self):
        ui = self.ui
        if ui.nSpectraRadioButton.isChecked():
            ui.exportPeriodPushButton.setEnabled(False)
        elif ui.nMinutesRadioButton.isChecked():
            ui.exportPeriodPushButton.setEnabled(True)
        elif ui.periodRadioButton.isChecked():
            ui.exportPeriodPushButton.setEnabled(
                self.info.periods is not None)

    @state_node
    def importPeriod(self):
        success, file = UiUtils.openfile(
            "Select one period file", "CSV files(*.csv)")
        if not success:
            return

        def func():
            ret = []
            with open(file, 'r') as f:
                reader = csv.reader(f)
                it = iter(reader)
                next(it)  # skip row
                time_parser = utils.TimeParser()
                for row in it:
                    item = PeriodItem(time_parser.parse(
                        row[0]), time_parser.parse(row[1]))
                    ret.append(item)
            return ret
        self.info.periods = yield func, "Read periods"
        if not self.ui.exportPeriodPushButton.isEnabled():
            self.ui.exportPeriodPushButton.setEnabled(True)

    @state_node
    def exportPeriod(self):
        success, file = UiUtils.savefile("Save to", "CSV files(*.csv)")
        if not success:
            return

        ui = self.ui
        period_checked = ui.periodRadioButton.isChecked()
        minutes_checked = ui.nMinutesRadioButton.isChecked()
        start_point = ui.startDateTimeEdit.dateTime().toPyDateTime()
        end_point = ui.endDateTimeEdit.dateTime().toPyDateTime()
        interval = timedelta(minutes=ui.nMinutesDoubleSpinBox.value())

        def func():
            if period_checked:
                periods = self.info.periods
            elif minutes_checked:
                def generator():
                    for s, e in generage_periods(start_point, end_point, interval):
                        yield PeriodItem(s, e)
                periods = generator()
            else:
                periods: List[PeriodItem] = []
            with open(file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(('start time', 'end time'))
                for p in periods:
                    writer.writerow((str(p.start_time), str(p.end_time)))

        yield func, "exporting periods"

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
        data = event.mimeData()
        text = data.text().splitlines()
        if text and text[0].startswith("file:///"):
            event.setDropAction(QtCore.Qt.DropAction.LinkAction)
            event.accept()

    def tableDragMoveEvent(self, event: QtGui.QDragMoveEvent):
        event.accept()

    @state_node(withArgs=True)
    def tableDropEvent(self, event: QtGui.QDropEvent):
        paths = event.mimeData().text().splitlines()
        def func():
            pathlist = self.pathlist
            for file in paths:
                p = pathlib.Path(file[len("file:///"):])
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
                interval = timedelta(
                    minutes=ui.nMinutesDoubleSpinBox.value())
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_time_interval,
                               paths, interval, polarity, time_range)
            elif ui.periodRadioButton.isChecked():
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_periods,
                               paths, polarity, [(p.start_time, p.end_time)for p in self.info.periods])
        else:
            func = partial(FileSpectrumInfo.generate_infos_from_paths,
                           paths, polarity, time_range)

        return func
