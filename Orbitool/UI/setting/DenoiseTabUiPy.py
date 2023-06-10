from PyQt5 import QtCore, QtWidgets
from .DenoiseTabUi import Ui_Form
from Orbitool.config import _Setting
from Orbitool.utils.formula import Formula
from .common import BaseTab


class Tab(BaseTab):
    def __init__(self, parent: QtWidgets.QWidget, setting: _Setting) -> None:
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        self.init(setting)

    def init(self, setting: _Setting):
        ui = self.ui

        denoise = setting.denoise

        ui.noiseDifferentColorCheckBox.setChecked(denoise.plot_noise_in_diff_color)
        ui.peaksPlainTextEdit.setPlainText(', '.join(denoise.noise_formulas))

    def stash_setting(self, setting: _Setting):
        ui = self.ui
        denoise = setting.denoise
        denoise.plot_noise_in_diff_color = ui.noiseDifferentColorCheckBox.isChecked()
        formulas = ui.peaksPlainTextEdit.toPlainText().replace(",", "\t").split()
        denoise.noise_formulas = sorted(formulas, key=lambda s: Formula(s).mass())
        
