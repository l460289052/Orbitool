from multiprocessing import cpu_count
import typing
from PyQt5 import QtCore, QtWidgets
from .FileTabUi import Ui_Form
from Orbitool.config import _Setting
from .common import BaseTab
from datetime import datetime


class Tab(BaseTab):
    def __init__(self, parent: QtWidgets.QWidget, setting: _Setting) -> None:
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.init(setting)

    def init(self, setting: _Setting):
        ui = self.ui

        file = setting.file

        ui.dotnetDriverComboBox.clear()
        ui.dotnetDriverComboBox.addItem(".Net Framework (4.7.2, 4.8.*)", ".net framework")
        ui.dotnetDriverComboBox.addItem(".Net Core (>=3.1)", ".net core")
        match file.dotnet_driver:
            case ".net framework":
                index = 0
            case ".net core":
                index = 1
        ui.dotnetDriverComboBox.setCurrentIndex(index)

    def stash_setting(self, setting: _Setting):
        ui = self.ui
        file = setting.file
        file.dotnet_driver = ui.dotnetDriverComboBox.currentData()
