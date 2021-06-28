from typing import Union, Optional, List
from .. import config
from collections import deque

from PyQt5 import QtWidgets, QtCore
import numpy as np
import matplotlib.ticker

from . import NoiseUi
from .utils import showInfo, get_tablewidget_selected_row, set_header_sizes
from .manager import Manager, state_node, Thread
from . import component
from .component import factory

from ..structures import file, workspace
from ..structures.file import SpectrumInfo
from ..structures.spectrum import Spectrum
from .. import functions
from ..functions import binary_search, spectrum as spectrum_func
from ..utils.formula import Formula


class Widget(QtWidgets.QWidget, NoiseUi.Ui_Form):
    selected_spectrum_average = QtCore.pyqtSignal()
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.setupUi(self)
        self.addPushButton.clicked.connect(self.addFormula)
        self.delPushButton.clicked.connect(self.delFormula)

        manager.inited.connect(self.showNoiseFormula)

    def setupUi(self, Form):
        super().setupUi(Form)

        set_header_sizes(self.paramTableWidget.horizontalHeader(), [
                         100, 100, 150, 150])
        self.plot = component.Plot(self.widget)
        self.toolBox.setCurrentIndex(0)
        self.showAveragePushButton.clicked.connect(self.showSelectedSpectrum)
        self.calculateNoisePushButton.clicked.connect(self.calcNoise)
        self.denoisePushButton.clicked.connect(self.denoise)

    @property
    def noise(self):
        return self.manager.workspace.noise_tab

    def showNoiseFormula(self):
        widget = self.tableWidget
        widget.clearContents()
        widget.setRowCount(0)
        formulas = self.noise.info.noise_formulas
        widget.setRowCount(len(formulas))
        for i, formula in enumerate(formulas):
            widget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                str(formula.formula)))
            dsb = QtWidgets.QSpinBox()
            dsb.setMinimum(1)
            dsb.setMaximum(50)
            dsb.setValue(formula.delta)
            widget.setCellWidget(i, 1, dsb)
            widget.setItem(i, 2, QtWidgets.QTableWidgetItem(
                format(formula.formula.mass(), ".6f")))

    @state_node
    def showSelectedSpectrum(self):
        workspace = self.manager.workspace
        time = workspace.spectra_list.info.selected_start_time
        info_list = workspace.spectra_list.info.file_spectrum_info_list
        if time is None:
            if config.default_select:
                index = 0
            else:
                showInfo("Please select a spectrum in spectra list")
                return None
        else:
            index = binary_search.indexNearest(
                info_list, time, method=lambda x, i: x[i].start_time)

        left = index
        while info_list[left].average_index != 0:
            index -= 1
        right = index + 1
        while info_list[right].average_index != 0:
            right += 1

        infos: List[SpectrumInfo] = list(info_list[left:right])

        def read_and_average():
            if len(spectrums := [spectrum for info in infos if (spectrum := info.get_spectrum_from_info(with_minutes=True)) is not None]) > 0:
                spectrums = [(*functions.spectrum.removeZeroPositions(
                    spectrum[0], spectrum[1]), spectrum[2]) for spectrum in spectrums]
                mass, intensity = functions.spectrum.averageSpectra(
                    spectrums, infos[0].rtol, True)
                spectrum = Spectrum(file_path='', mass=mass, intensity=intensity,
                                    start_time=infos[0].start_time, end_time=infos[-1].end_time)
                return True, spectrum
            else:
                return False, None

        success, spectrum = yield read_and_average

        if success:
            self.noise.info.current_spectrum = spectrum
            self.selected_spectrum_average.emit()
            self.plot.ax.plot(spectrum.mass, spectrum.intensity)
            self.plot.canvas.draw()
            self.show()
        else:
            showInfo("failed")

    @state_node
    def addFormula(self):
        formula = Formula(self.lineEdit.text())
        self.noise.info.noise_formulas.append(
            workspace.NoiseFormulaParameter(formula=formula))
        self.showNoiseFormula()

    addFormula.except_node(showNoiseFormula)

    @state_node
    def delFormula(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        indexes.reverse()
        for index in indexes:
            del self.noise.info.noise_formulas[index]
        self.showNoiseFormula()

    delFormula.except_node(showNoiseFormula)

    @state_node
    def calcNoise(self):
        info = self.noise.info
        spectrum = info.current_spectrum

        quantile = self.quantileDoubleSpinBox.value()
        n_sigma = self.nSigmaDoubleSpinBox.value()

        subtrace = self.substractCheckBox.isChecked()

        mass_dependent = self.sizeDependentCheckBox.isChecked()

        mass_points = np.array([f.formula.mass()
                                for f in self.noise.noise_formulas])
        mass_point_deltas = np.array([self.tableWidget.cellWidget(
            i, 1).value() for i in range(self.tableWidget.rowCount())], dtype=np.int)

        def func():
            poly, std, slt, params = spectrum_func.getNoiseParams(
                spectrum.mass, spectrum.intensity, quantile, mass_dependent, mass_points, mass_point_deltas)
            noise, LOD = spectrum_func.noiseLODFunc(
                spectrum.mass, poly, params, mass_points, mass_point_deltas, n_sigma)
            return poly, std, slt, params, noise, LOD

        info.poly_coef, info.global_noise_std, slt, params, info.noise, info.LOD = yield func

        info.n_sigma = self.nSigmaDoubleSpinBox.value()

        ind: np.ndarray = slt.cumsum() - 1
        formula_params = info.noise_formulas
        for index, (i, s) in enumerate(zip(ind, slt)):
            p = formula_params[index]
            p.selected = s
            if s:
                p.param = params[i]
            formula_params[index] = p

        self.showNoise()

    def showNoise(self):
        info = self.noise.info
        n_sigma = self.nSigmaDoubleSpinBox.value()
        std = info.global_noise_std

        global_noise = np.polynomial.polynomial.polyval(
            200, info.poly_coef)
        global_lod = global_noise + n_sigma * std

        checkeds = [True]
        names = ["global"]
        noises = [global_noise]
        lods = [global_lod]
        for param in info.noise_formulas:
            checkeds.append(param.selected)
            names.append(str(param.formula))
            noise, lod = spectrum_func.getShownNoiseLODFromParam(
                param.param, n_sigma)
            noises.append(noise)
            lods.append(lod)

        table = self.paramTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(checkeds))

        for i, (checked, name, noise, lod) in enumerate(zip(checkeds, names, noises, lods)):
            checkBox = factory.CheckBoxFactory(checked)
            checkBox.setDisabled(True)
            table.setCellWidget(i, 0, checkBox)

            table.setItem(i, 1, QtWidgets.QTableWidgetItem(name))

            spinbox = factory.DoubleSpinBoxFactory(0, 1e11, 1, 1, noise)
            table.setCellWidget(i, 2, spinbox)

            spinbox = factory.DoubleSpinBoxFactory(0, 1e11, 1, 1, noise)
            table.setCellWidget(i, 3, spinbox)

        self.toolBox.setCurrentWidget(self.paramTool)
        table.show()
        self.plotNoise()

    def plotNoise(self):
        noise_tab = self.noise
        spectrum = noise_tab.current_spectrum

        is_log = self.yLogCheckBox.isChecked()
        plot = self.plot
        ax = plot.ax
        ax.clear()

        ax.set_yscale('log' if is_log else 'linear')

        ax.axhline(color='k', linewidth=0.5)
        ax.yaxis.set_tick_params(rotation=45)

        if not is_log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.plot(spectrum.mass, spectrum.intensity,
                linewidth=1, color="#BF2138", label="Spectrum")
        ax.plot(spectrum.mass, noise_tab.LOD,
                linewidth=1, color='k', label='LOD')
        ax.plot(spectrum.mass, noise_tab.noise,
                linewidth=1, color='b', label='noise')
        ax.legend(loc='upper right')

        x_min = spectrum.mass[0]
        x_max = spectrum.mass[-1]
        ymax = np.polynomial.polynomial.polyval(
            x_max, noise_tab.poly_coef) + noise_tab.n_sigma * noise_tab.global_noise_std
        if is_log:
            ymin = np.polynomial.polynomial.polyval(
                [x_min, x_max], noise_tab.poly_coef).min()
            ymin *= 0.5
            ymax *= 10
        else:
            ymin = 0
            ymax *= 5
        ax.set_ylim(ymin, ymax)
        plot.canvas.draw()

    @state_node
    def denoise(self):
        if self.dependentCheckBox.isChecked():
            pass
        else:
            pass
