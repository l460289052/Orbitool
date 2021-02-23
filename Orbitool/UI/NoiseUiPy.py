from typing import Union, Optional, List
from collections import deque

from PyQt5 import QtWidgets, QtCore
import numpy as np

from . import NoiseUi
from .utils import showInfo, get_tablewidget_selected_row
from .manager import BaseWidget, state_node, Thread
from . import component

from Orbitool.structures import file, workspace
from Orbitool.structures.file import SpectrumInfo
from Orbitool.structures.spectrum import Spectrum
from Orbitool import functions
from Orbitool.functions import binary_search, spectrum as spectrum_func
from Orbitool.utils.formula import Formula


class Widget(QtWidgets.QWidget, NoiseUi.Ui_Form, BaseWidget):
    selected_spectrum_average = QtCore.pyqtSignal()

    def __init__(self, widget_root, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        self.widget_root = widget_root

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = component.Plot(self.widget)
        self.toolBox.setCurrentIndex(0)
        self.showAveragePushButton.clicked.connect(self.showSelectedSpectrum)
        self.calculateNoisePushButton.clicked.connect(self.calcNoise)

        self.addPushButton.clicked.connect(self.addFormula)
        self.delPushButton.clicked.connect(self.delFormula)

    @property
    def noise(self):
        return self.current_workspace.noise_tab

    def showNoiseFormula(self):
        widget = self.tableWidget
        widget.clearContents()
        widget.setRowCount(0)
        formulas: List[workspace.NoiseFormulaParameter] = self.noise.noise_formulas
        widget.setRowCount(len(formulas))
        for i, formula in enumerate(formulas):
            widget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                str(formula.formula)))
            dsb = QtWidgets.QDoubleSpinBox()
            dsb.setValue(formula.delta)
            widget.setCellWidget(i, 1, dsb)
            widget.setItem(i, 2, QtWidgets.QTableWidgetItem(
                str(formula.formula.mass())))

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

        mass_points = [f.formula.mass() for f in self.noise.noise_formulas]
        # need to pass delta

        def func(spectrum: Spectrum):
            spectrum_func.getNoiseParams(
                spectrum.mass, spectrum.intensity, quantile, mass_dependent, mass_points, )
        return Thread(func, (self.noise.current_spectrum))

    @state_node
    def addFormula(self):
        formula = Formula(self.lineEdit.text())
        self.noise.noise_formulas.extend(
            [workspace.NoiseFormulaParameter(formula, 5)])
        self.showNoiseFormula()

    @addFormula.except_node
    def addFormula(self):
        self.showNoiseFormula()

    @state_node
    def delFormula(self):
        index = get_tablewidget_selected_row(self.tableWidget)
        del self.noise.noise_formulas[index]
        self.showNoiseFormula()

    @delFormula.except_node
    def delFormula(self):
        self.showNoiseFormula()
