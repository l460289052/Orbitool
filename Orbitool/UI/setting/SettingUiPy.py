import typing
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget
from .SettingUi import Ui_Dialog

class Dialog(QtWidgets.QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.init()

    def init(self):
        listWidget = self.ui.listWidget
        listWidget.addItem(QtWidgets.QListWidgetItem(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView), "123"
        ))

