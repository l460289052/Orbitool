import os
import csv
from datetime import datetime, timedelta
from functools import partial
from typing import List, Optional, Union, Iterable

from PyQt5 import QtCore, QtWidgets

from .. import utils
from ..structures.file import Path, PathList, FileSpectrumInfo, PeriodItem
from ..functions.file import generage_periods
from ..workspace import UiNameGetter, UiState
from . import FileUi
from . import utils as UiUtils
from .manager import Manager, Thread, state_node
from .utils import set_header_sizes, showInfo


class Widget(QtWidgets.QWidget, FileUi.Ui_Form):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.setupUi(self)

        manager.init_or_restored.connect(self.init_or_restore)
        manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(self)

        set_header_sizes(self.tableWidget.horizontalHeader(), [150, 100, 100])

        self.addFilePushButton.clicked.connect(self.addThermoFile)
        self.addFolderPushButton.clicked.connect(self.addFolder)
        self.removeFilePushButton.clicked.connect(self.removePath)

        self.timeAdjustPushButton.clicked.connect(self.adjust_time)

        self.nSpectraRadioButton.clicked.connect(self.radioButtonChanged)
        self.nMinutesRadioButton.clicked.connect(self.radioButtonChanged)
        self.periodRadioButton.clicked.connect(self.radioButtonChanged)

        self.periodImportToolButton.clicked.connect(self.importPeriod)
        self.exportPeriodPushButton.clicked.connect(self.exportPeriod)

        self.selectedPushButton.clicked.connect(self.processSelected)
        self.allPushButton.clicked.connect(self.processAll)

    @property
    def file(self):
        return self.manager.workspace.file_tab

    @property
    def pathlist(self) -> PathList:
        return self.manager.workspace.file_tab.info.pathlist

    def init_or_restore(self):
        self.showPaths()
        self.file.ui_state.set_state(self)

    def updateState(self):
        self.file.ui_state.fromComponents(self, [
            self.recursionCheckBox,
            self.nSpectraRadioButton,
            self.nMinutesRadioButton,
            self.periodRadioButton,
            self.nSpectraSpinBox,
            self.nMinutesDoubleSpinBox,
            self.autoTimeCheckBox,
            self.startDateTimeEdit,
            self.endDateTimeEdit,
            self.rtolDoubleSpinBox,
            self.positiveRadioButton,
            self.negativeRadioButton,
            self.averageCheckBox])

    @state_node(mode='n')
    def radioButtonChanged(self):
        if self.nSpectraRadioButton.isChecked():
            self.exportPeriodPushButton.setEnabled(False)
        elif self.nMinutesRadioButton.isChecked():
            self.exportPeriodPushButton.setEnabled(True)
        elif self.periodRadioButton.isChecked():
            self.exportPeriodPushButton.setEnabled(
                self.file.info.periods is not None)

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
                for row in it:
                    item = PeriodItem(datetime.fromisoformat(
                        row[0].replace('/', '-')), datetime.fromisoformat(row[1].replace('/', '-')))
                    ret.append(item)
            return ret
        self.file.info.periods = yield func, "Read periods"
        if not self.exportPeriodPushButton.isEnabled():
            self.exportPeriodPushButton.setEnabled(True)

    @state_node
    def exportPeriod(self):
        success, file = UiUtils.savefile("Save to", "CSV files(*.csv)")
        if not success:
            return

        period_checked = self.periodRadioButton.isChecked()
        minutes_checked = self.nMinutesRadioButton.isChecked()
        start_point = self.startDateTimeEdit.dateTime().toPyDateTime()
        end_point = self.endDateTimeEdit.dateTime().toPyDateTime()
        interval = timedelta(minutes=self.nMinutesDoubleSpinBox.value())

        def func():
            if period_checked:
                periods = self.file.info.periods
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
            for path in manager.tqdm(utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.recursionCheckBox.isChecked())):
                pathlist.addThermoFile(path)
            pathlist.sort()

        yield func, "read folders"

        self.showPaths()

    @addFolder.except_node
    def addFolder(self):
        self.showPaths()

    @state_node
    def removePath(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.tableWidget)
        self.pathlist.rmPath(indexes)
        self.showPaths()

    @removePath.except_node
    def removePath(self):
        self.showPaths()

    def showPaths(self):
        table = self.tableWidget
        pathlist = self.pathlist
        table.setRowCount(0)
        table.setRowCount(len(pathlist))

        for i, f in enumerate(pathlist):
            v = [os.path.split(f.path)[1], f.startDatetime.replace(microsecond=0),
                 f.endDatetime.replace(microsecond=0), f.path]
            for j, vv in enumerate(v):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(vv)))

        if self.autoTimeCheckBox.isChecked():
            time_start, time_end = self.pathlist.timeRange
            if time_start is None:
                return
            self.startDateTimeEdit.setDateTime(time_start)
            self.endDateTimeEdit.setDateTime(time_end)

    @state_node
    def adjust_time(self):
        slt = UiUtils.get_tablewidget_selected_row(self.tableWidget)
        paths = self.pathlist.subList(slt)
        start, end = paths.timeRange
        if start is None:
            return
        self.startDateTimeEdit.setDateTime(start)
        self.endDateTimeEdit.setDateTime(end)

    @state_node
    def processSelected(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.tableWidget)
        if len(indexes) == 0:
            return None

        paths = self.pathlist.subList(indexes)
        self.file.info.spectrum_infos = yield self.processPaths(paths.paths), "get infomations from selected spectra"

        self.callback.emit()

    @state_node
    def processAll(self):
        self.file.info.spectrum_infos = yield self.processPaths(self.pathlist.paths), "get infomations from spectra"

        self.callback.emit()

    def processPaths(self, paths: List[Path]):
        time_range = (self.startDateTimeEdit.dateTime().toPyDateTime(),
                      self.endDateTimeEdit.dateTime().toPyDateTime())

        paths = self.manager.tqdm(paths)

        self.file.info.rtol = self.rtolDoubleSpinBox.value() * 1e-6
        if self.positiveRadioButton.isChecked():
            polarity = 1
        elif self.negativeRadioButton.isChecked():
            polarity = -1
        else:
            raise ValueError("Please select a polarity")

        if self.averageCheckBox.isChecked():
            if self.nSpectraRadioButton.isChecked():
                num = self.nSpectraSpinBox.value()
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_number,
                               paths, num, polarity, time_range)
            elif self.nMinutesRadioButton.isChecked():
                interval = timedelta(
                    minutes=self.nMinutesDoubleSpinBox.value())
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_time_interval,
                               paths, interval, polarity, time_range)
            elif self.periodRadioButton.isChecked():
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_periods,
                               paths, polarity, [(p.start_time, p.end_time)for p in self.file.info.periods])
        else:
            func = partial(FileSpectrumInfo.generate_infos_from_paths,
                           paths, polarity, time_range)

        return func
