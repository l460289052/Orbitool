from typing import Union, Optional
from . import FileUi, utils as UiUtils
from .utils import showInfo, set_header_sizes
from .manager import BaseWidget, state_node
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

    @state_node
    def addFile(self):
        files = UiUtils.openfiles(
            "Select one or more files", "RAW files(*.RAW)")
        fileList = self.workspace.fileList
        for f in files:
            fileList.addFile(f)
        self.showFiles()

    @addFile.except_node
    def addFile(self):
        self.showFiles()

    @state_node
    def addFolder(self):
        ret, folder = UiUtils.openfolder("Select one folder")
        if not ret:
            return
        fileList = self.workspace.fileList
        for path in utils.files.FolderTraveler(folder, ext=".RAW", recurrent=self.recursionCheckBox.isChecked()):
            fileList.addFile(path)
        self.showFiles()

    @addFolder.except_node
    def addFolder(self):
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
