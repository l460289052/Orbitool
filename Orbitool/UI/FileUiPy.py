import os
from datetime import datetime, timedelta
from functools import partial
from typing import List, Optional, Union

from PyQt5 import QtCore, QtWidgets

from .. import utils
from ..structures.file import Path, PathList, FileSpectrumInfo
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

        manager.inited_or_restored.connect(self.init_or_restore)
        manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(self)

        set_header_sizes(self.tableWidget.horizontalHeader(), [150, 100, 100])

        self.addFilePushButton.clicked.connect(self.addThermoFile)
        self.addFolderPushButton.clicked.connect(self.addFolder)
        self.removeFilePushButton.clicked.connect(self.removePath)
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
        getter = UiNameGetter(self)
        getter.register_components([
            self.recursionCheckBox,
            self.nSpectraRadioButton,
            self.nMinutesRadioButton,
            self.nSpectraSpinBox,
            self.nMinutesDoubleSpinBox,
            self.autoTimeCheckBox,
            self.startDateTimeEdit,
            self.endDateTimeEdit,
            self.rtolDoubleSpinBox,
            self.positiveRadioButton,
            self.negativeRadioButton,
            self.averageCheckBox])
        self.file.ui_state = UiState.FactoryStateGetter(
            self, getter.registered)

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

        length = yield func

        showInfo(str(length))
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

        def func():
            for path in utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.recursionCheckBox.isChecked()):
                pathlist.addThermoFile(path)
            pathlist.sort()

        yield func

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
            v = [os.path.split(f.path)[1], f.startDatetime,
                 f.endDatetime, f.path]
            for j, vv in enumerate(v):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(vv)))


        if self.autoTimeCheckBox.isChecked():
            time_start, time_end = self.pathlist.timeRange
            if time_start is None:
                return
            self.startDateTimeEdit.setDateTime(time_start)
            self.endDateTimeEdit.setDateTime(time_end)

    @state_node
    def processSelected(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.tableWidget)
        if len(indexes) == 0:
            return None

        paths = self.pathlist.subList(indexes)
        self.file.info.spectrum_infos = yield self.processPaths(paths.paths)

        self.callback.emit()

    @state_node
    def processAll(self):
        self.file.info.spectrum_infos = yield self.processPaths(self.pathlist.paths)

        self.callback.emit()

    def processPaths(self, paths: List[Path]):
        time_range = (self.startDateTimeEdit.dateTime().toPyDateTime(),
                      self.endDateTimeEdit.dateTime().toPyDateTime())

        rtol = self.rtolDoubleSpinBox.value() * 1e-6
        if self.positiveRadioButton.isChecked():
            polarity = 1
        elif self.negativeRadioButton.isChecked():
            polarity = -1
        else:
            raise ValueError("Please select a polarity")

        if self.averageCheckBox.isChecked():
            if self.nSpectraRadioButton.isChecked():
                pass
            elif self.nMinutesRadioButton.isChecked():
                interval = timedelta(
                    minutes=self.nMinutesDoubleSpinBox.value())
                func = partial(FileSpectrumInfo.generate_infos_from_paths_by_time_interval,
                               paths, rtol, interval, polarity, time_range)
        else:
            func = partial(FileSpectrumInfo.generate_infos_from_paths,
                           paths, rtol, polarity, time_range)

        return func
