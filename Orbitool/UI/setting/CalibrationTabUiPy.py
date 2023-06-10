from PyQt5 import QtCore, QtWidgets
from .CalibrationTabUi import Ui_Form
from Orbitool.config import _Setting
from .common import BaseTab


class Tab(BaseTab):
    def __init__(self, parent: QtWidgets.QWidget, setting: _Setting) -> None:
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.init(setting)

    def init(self, setting: _Setting):
        ui = self.ui

        cali = setting.calibration

        ui.dragDropReplaceCheckBox.setChecked(cali.dragdrop_ion_replace)

    def stash_setting(self, setting: _Setting):
        ui = self.ui
        cali = setting.calibration
        cali.dragdrop_ion_replace = ui.dragDropReplaceCheckBox.isChecked()
