from typing import Union, Optional
from datetime import datetime

from . import FileUi, utils as UiUtils
from .utils import showInfo, set_header_sizes, get_tablewidget_selected_row
from .manager import BaseWidget, state_node, Thread
from PyQt5 import QtWidgets, QtCore
import os

from Orbitool.structures import file
from Orbitool import utils


class Widget(QtWidgets.QWidget, FileUi.Ui_Form, BaseWidget):
    def __init__(self, widget_root: BaseWidget, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.widget_root = widget_root
        self.setupUi(self)

        set_header_sizes(self.tableWidget.horizontalHeader(), [150, 100, 100])

        self.addFilePushButton.clicked.connect(self.addFile)
        self.addFolderPushButton.clicked.connect(self.addFolder)
        self.removeFilePushButton.clicked.connect(self.removeFile)

    @state_node
    def addFile(self):
        files = UiUtils.openfiles(
            "Select one or more files", "RAW files(*.RAW)")
        fileList = self.workspace.fileList

        def func():
            for f in files:
                fileList.addFile(f)
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
        fileList = self.workspace.fileList

        def func():
            for path in utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.recursionCheckBox.isChecked()):
                fileList.addFile(path)
        return Thread(func)

    @addFolder.thread_node
    def addFolder(self, result, args):
        self.showFiles()

    @addFolder.except_node
    def addFolder(self):
        self.showFiles()

    @state_node
    def removeFile(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        self.workspace.fileList.rmFile(indexes)
        self.showFiles()

    @removeFile.except_node
    def removeFile(self):
        self.showFiles()

    def showFiles(self):
        table = self.tableWidget
        fileList = self.workspace.fileList
        table.setRowCount(0)
        table.setRowCount(len(fileList))

        for i, f in enumerate(fileList):
            v = [os.path.split(f.path)[1], f.startDatetime,
                 f.endDatetime, f.path]
            for j, vv in enumerate(v):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(vv)))

        table.show()

        if self.checkBox.isChecked():
            time_start, time_end = self.workspace.fileList.timeRange()
            if time_start is None:
                return
            self.startDateTimeEdit.setDateTime(time_start)
            self.endDateTimeEdit.setDateTime(time_end)
