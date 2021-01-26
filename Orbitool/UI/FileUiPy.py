from typing import Union, Optional
from . import FileUi, utils as UiUtils, baseWidget
from PyQt5 import QtWidgets, QtCore
import os


class Widget(QtWidgets.QWidget, FileUi.Ui_Form, baseWidget):
    def __init__(self, getWorkspace, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.getWorkspace = getWorkspace
        self.addFilePushButton.clicked.connect(self.addFile)
        self.addFolderPushButton.clicked.connect(self.addFolder)

    def addFile(self):
        files = UiUtils.openfiles(
            "Select one or more files", "RAW files(*.RAW)")
        fileList = self.workspace.fileList
        for f in files:
            fileList.addFile(f)
        self.showFiles()
        
    def addFolder(self);


    def showFiles(self):
        table = self.tableWidget
        fileList = self.workspace.fileList
        table.setRowCount(0)
        table.setRowCount(len(fileList))

        for i, f in enumerate(fileList):
            v = [os.path.split(f['path'])[1], f[2], f[3], f[0]]
            for j, vv in enumerate(v):
                table.setItem(i,j,QtWidgets.QTableWidgetItem(vv))
        
        table.show()

                
