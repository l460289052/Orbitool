from typing import Union, Optional

from PyQt5 import QtWidgets, QtCore
import numpy as np

from . import NoiseUi
from .utils import showInfo
from .manager import BaseWidget, state_node, Thread
from . import component

from Orbitool.structures.file import SpectrumInfo


class Widget(QtWidgets.QWidget, NoiseUi.Ui_Form, BaseWidget):
    selected_spectrum_average = QtCore.pyqtSignal()

    def __init__(self, widget_root, parent: Optional['QWidget'] = None) -> None:
        super().__init__()
        self.setupUi(self)
        self.widget_root = widget_root

        self.toolBox.setCurrentIndex(0)
        self.showAveragePushButton.clicked.connect(self.showSelectedSpectrum)
        self.calculateNoisePushButton.clicked.connect(self.calcNoise)

    def setupUi(self, Form):
        super().setupUi(Form)
        self.plot = component.Plot(self.widget)

    @property
    def noise(self):
        return self.current_workspace.noise_tab

    @state_node
    def showSelectedSpectrum(self):
        workspace = self.current_workspace
        index = workspace.spectra_list.selected_spectrum_index
        if index is None:
            showInfo("Please select a spectrum in spectra list")
            return None
        spectrum_info: SpectrumInfo = workspace.spectra_list.file_spectrum_info_list[index]
        return Thread(spectrum_info.get_spectrum, (workspace.noise_tab.current_spectrum, ))

    @showSelectedSpectrum.thread_node
    def showSelectedSpectrum(self, result, args):
        self.selected_spectrum_average.emit()
        spectrum = self.noise.current_spectrum
        self.plot.ax.plot(spectrum.mz, spectrum.intensity)
        self.plot.canvas.draw()
        self.show()

    @state_node
    def calcNoise(self):
        workspace = self.current_workspace
        index = workspace.spectra_list.selected_spectrum_index
        spectrum_info: SpectrumInfo = workspace.spectra_list.file_spectrum_info_list[index]
        spectrum = self.noise.current_spectrum

        quantile = self.quantileDoubleSpinBox.value()
        n_sigma = self.nSigmaDoubleSpinBox.value()

        subtrace = self.substractCheckBox.isChecked()

        mass_dependent = self.sizeDependentCheckBox.isChecked()
        monomer = self.monomerNoiseCheckBox.isChecked()
        dimer = self.dimerNoiseCheckBox.isChecked()
        flags = (mass_dependent, monomer, dimer)
        

        def func():
            spectrum_info.get_spectrum(spectrum)
            # params, ret_flags = Orbitool.
            # 需要和润龙商量一下参数，因为这样的话，先设置了一个之后进行校准的参数就会影响到之后相同质谱的参数，不太符合常理
        return Thread(func)
