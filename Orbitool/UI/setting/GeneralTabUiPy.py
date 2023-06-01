import typing
from PyQt5 import QtCore, QtWidgets
from .GeneralTabUi import Ui_Form
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
        ui.defaultSelectCheckBox.setChecked(setting.default_select)
        ui.timeFormatLineEdit.textChanged.connect(self.change_time_format)
        ui.timeFormatLineEdit.setText(setting.format_time)
        ui.exportTimeFormatLineEdit.textChanged.connect(self.change_export_time_format)
        ui.exportTimeFormatLineEdit.setText(setting.format_export_time)

    def stash_setting(self, setting: _Setting):
        ui = self.ui
        setting.default_select = ui.defaultSelectCheckBox.isChecked()
        setting.format_time = ui.timeFormatLineEdit.text()
        setting.format_export_time = ui.exportTimeFormatLineEdit.text()

    def change_time_format(self, text: str):
        try:
            s = f"example: {datetime.now().strftime(text)}"
        except Exception as e:
            s = f"example: {e}"
        self.ui.timeFormatShowLabel.setText(s)

    def change_export_time_format(self, text: str):
        try:
            s = f"example: {datetime.now().strftime(text)}"
        except Exception as e:
            s = f"example: {e}"
        self.ui.exportTimeFormatShowLabel.setText(s)