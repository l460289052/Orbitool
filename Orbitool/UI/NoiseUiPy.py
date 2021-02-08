from typing import Union, Optional, List
from collections import deque

from PyQt5 import QtWidgets, QtCore
import numpy as np

from . import NoiseUi
from .utils import showInfo
from .manager import BaseWidget, state_node, Thread
from . import component

from Orbitool.structures import file
from Orbitool.structures.file import SpectrumInfo
from Orbitool.structures.spectrum import Spectrum
from Orbitool import functions
from Orbitool.functions import binary_search


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
        time = workspace.spectra_list.selected_start_time
        if time is None:
            showInfo("Please select a spectrum in spectra list")
            return None

        info_list = workspace.spectra_list.file_spectrum_info_list
        index = binary_search.indexNearest_np(
            info_list.get_column("start_time"), np.datetime64(time, 's'))
        left = index
        while info_list[left].average_index != 0:
            index -= 1
        right = index + 1
        while info_list[right].average_index != 0:
            right += 1

        infos: List[SpectrumInfo] = list(info_list[left:right])

        def func(infos: List[SpectrumInfo], target_spectrum: Spectrum):

            if len(spectrums := [spectrum for info in infos if (spectrum := info.get_spectrum_from_info(with_minutes=True)) is not None]) > 0:
                spectrums = [(*functions.spectrum.removeZeroPositions(
                    spectrum[0], spectrum[1]), spectrum[2]) for spectrum in spectrums]
                mass, intensity = functions.spectrum.averageSpectra(
                    spectrums, infos[0].rtol, True)
                target_spectrum.file_path = ''
                target_spectrum.mass = mass
                target_spectrum.intensity = intensity
                target_spectrum.start_tTime = infos[0].start_time
                target_spectrum.end_time = infos[-1].end_time
                return True
            else:
                return False

        return Thread(func, (infos, self.noise.current_spectrum))

    @showSelectedSpectrum.thread_node
    def showSelectedSpectrum(self, result, args):
        self.selected_spectrum_average.emit()
        spectrum = self.noise.current_spectrum
        self.plot.ax.plot(spectrum.mass, spectrum.intensity)
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
