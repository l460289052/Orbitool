from typing import Union, Optional
from datetime import datetime, timedelta
from functools import partial

from . import FileUi, utils as UiUtils
from .utils import showInfo, set_header_sizes
from .manager import BaseWidget, state_node, Thread
from PyQt5 import QtWidgets, QtCore
import os

from ..structures import file
from .. import utils


class Widget(QtWidgets.QWidget, FileUi.Ui_Form, BaseWidget):
    callback = QtCore.pyqtSignal()

    def __init__(self, widget_root: BaseWidget, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.widget_root = widget_root
        self.setupUi(self)

        set_header_sizes(self.tableWidget.horizontalHeader(), [150, 100, 100])

        self.addFilePushButton.clicked.connect(self.addFile)
        self.addFolderPushButton.clicked.connect(self.addFolder)
        self.removeFilePushButton.clicked.connect(self.removeFile)
        self.selectedPushButton.clicked.connect(self.processSelected)
        self.allPushButton.clicked.connect(self.processAll)

    @property
    def file_list(self) -> file.FileList:
        return self.current_workspace.file_list

    @state_node
    def addFile(self):
        files = UiUtils.openfiles(
            "Select one or more files", "RAW files(*.RAW)")
        file_list = self.file_list

        def func():
            for f in files:
                file_list.addFile(f)
            file_list.sort()
        return Thread(func)

    @addFile.thread_node
    def addFile(self, result, args):
        self.showFiles()

    @addFile.except_node
    def addFile(self):
        self.showFiles()

    @state_node
    def addFolder(self):
        ret, folder = UiUtils.openfolder("Select one folder")
        if not ret:
            return None
        file_list = self.file_list

        def func():
            for path in utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.recursionCheckBox.isChecked()):
                file_list.addFile(path)
            file_list.sort()
        return Thread(func)

    @addFolder.thread_node
    def addFolder(self, result, args):
        self.showFiles()

    @addFolder.except_node
    def addFolder(self):
        self.showFiles()

    @state_node
    def removeFile(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.tableWidget)
        self.file_list.rmFile(indexes)
        self.showFiles()

    @removeFile.except_node
    def removeFile(self):
        self.showFiles()

    def showFiles(self):
        table = self.tableWidget
        file_list = self.file_list
        table.setRowCount(0)
        table.setRowCount(len(file_list))

        for i, f in enumerate(file_list):
            v = [os.path.split(f.path)[1], f.startDatetime,
                 f.endDatetime, f.path]
            for j, vv in enumerate(v):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(vv)))

        table.show()

        if self.checkBox.isChecked():
            time_start, time_end = self.file_list.timeRange
            if time_start is None:
                return
            self.startDateTimeEdit.setDateTime(time_start)
            self.endDateTimeEdit.setDateTime(time_end)

    @state_node
    def processSelected(self):
        indexes = UiUtils.get_tablewidget_selected_row(self.tableWidget)
        if len(indexes) == 0:
            return None
        paths = self.file_list.files.get_column("path")[indexes]
        return self.processPaths(paths)

    @state_node
    def processAll(self):
        return self.processPaths(self.file_list.files.get_column("path"))

    @processSelected.thread_node
    def processSelected_end(self, *args):
        self.callback.emit()

    @processAll.thread_node
    def processAll_end(self, *args):
        self.callback.emit()

    def processPaths(self, paths):
        time_range = (self.startDateTimeEdit.dateTime().toPyDateTime(),
                      self.endDateTimeEdit.dateTime().toPyDateTime())

        rtol = self.rtolDoubleSpinBox.value() * 1e-6
        if self.positiveRadioButton.isChecked():
            polarity = 1
        elif self.negativeRadioButton.isChecked():
            polarity = -1
        else:
            raise ValueError("Please select a polarity")

        if self.averageYesRadioButton.isChecked():
            if self.nSpectraRadioButton.isChecked():
                pass
            elif self.nMinutesRadioButton.isChecked():
                interval = timedelta(
                    minutes=self.nMinutesDoubleSpinBox.value())
                func = partial(file.SpectrumInfo.generate_infos_from_paths_by_time_interval,
                               paths, rtol, interval, polarity, time_range)
        elif self.averageNoRadioButton.isChecked():
            func = partial(file.SpectrumInfo.generate_infos_from_paths,
                           paths, rtol, polarity, time_range)

        info_list = self.current_workspace.spectra_list.file_spectrum_info_list

        def thread_func():
            infos = func()
            info_list.clear()
            info_list.extend(infos)

        return Thread(thread_func)
