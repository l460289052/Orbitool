from collections import deque
from datetime import datetime
from typing import List, Optional, Union, Tuple, Generator, Iterable

import matplotlib.ticker
import numpy as np
from PyQt5 import QtCore, QtWidgets

from .. import config, workspace
from ..functions import spectrum as spectrum_func
from ..structures.file import FileSpectrumInfo
from ..structures.HDF5 import StructureListView
from ..structures.spectrum import Spectrum
from ..workspace import WorkSpace
from ..utils.formula import Formula
from . import NoiseUi, component
from .component import factory
from .manager import Manager, state_node, MultiProcess
from .utils import get_tablewidget_selected_row, set_header_sizes, showInfo


class ReadFromFile(MultiProcess):
    @staticmethod
    def func(data: Tuple[FileSpectrumInfo, Tuple[np.ndarray, np.ndarray, float]], **kwargs):
        info, (mz, intensity, time) = data
        mz, intensity = spectrum_func.removeZeroPositions(mz, intensity)
        spectrum = Spectrum(path=info.path, mz=mz, intensity=intensity,
                            start_time=info.start_time, end_time=info.end_time)
        return spectrum

    @ staticmethod
    def read(file: WorkSpace, **kwargs) -> Generator:
        for info in file.file_tab.info.spectrum_infos:
            yield info, info.get_spectrum_from_info(with_minutes=True)

    @ staticmethod
    def write(file: WorkSpace, rets: Iterable[Spectrum], **kwargs):
        tmp = StructureListView[Spectrum](file._obj, "tmp", True)
        tmp.h5_extend(rets)

        h5path = file.file_tab.raw_spectra.h5_path
        if h5path in file:
            del file[h5path]
        file._obj.move(tmp.h5_path, h5path)

    @ staticmethod
    def exception(file, **kwargs):
        if "tmp" in file:
            del file["tmp"]


class Widget(QtWidgets.QWidget, NoiseUi.Ui_Form):
    selected_spectrum_average = QtCore.pyqtSignal(Spectrum)
    callback = QtCore.pyqtSignal(tuple)

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

        manager.inited_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(Form)

        set_header_sizes(self.paramTableWidget.horizontalHeader(), [
                         100, 100, 150, 150])
        self.plot = component.Plot(self.widget)
        self.toolBox.setCurrentIndex(0)
        self.showAveragePushButton.clicked.connect(self.showSelectedSpectrum)
        self.addPushButton.clicked.connect(self.addFormula)
        self.delPushButton.clicked.connect(self.delFormula)
        self.calculateNoisePushButton.clicked.connect(self.calcNoise)
        self.recalculateNoisePushButton.clicked.connect(self.reclacNoise)
        self.denoisePushButton.clicked.connect(self.denoise)

    @property
    def noise(self):
        return self.manager.workspace.noise_tab

    def restore(self):
        self.showNoiseFormula()
        self.plotSelectSpectrum()
        self.showNoise()
        self.noise.ui_state.set_state(self)

    def updateState(self):
        self.noise.ui_state .fromComponents(self, [
            self.quantileDoubleSpinBox,
            self.nSigmaDoubleSpinBox,
            self.substractCheckBox,
            self.sizeDependentCheckBox,
            self.dependentCheckBox,
            self.yLogCheckBox])

    def showNoiseFormula(self):
        widget = self.tableWidget
        widget.clearContents()
        widget.setRowCount(0)
        formulas = self.noise.info.general_setting.noise_formulas
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
        index = self.manager.fetch_func("spectra list select")()
        info_list = workspace.file_tab.info.spectrum_infos

        left = index
        while info_list[left].average_index != 0:
            index -= 1
        right = index + 1
        while info_list[right].average_index != 0:
            right += 1

        infos: List[FileSpectrumInfo] = list(info_list[left:right])

        def read_and_average():
            if len(spectra := [spectrum for info in infos if (spectrum := info.get_spectrum_from_info(with_minutes=True)) is not None]) > 0:
                spectra = [(*spectrum_func.removeZeroPositions(
                    spectrum[0], spectrum[1]), spectrum[2]) for spectrum in spectra]
                mz, intensity = spectrum_func.averageSpectra(
                    spectra, infos[0].rtol, True)
                spectrum = Spectrum(path='none:', mz=mz, intensity=intensity,
                                    start_time=infos[0].start_time, end_time=infos[-1].end_time)
                return True, spectrum
            else:
                return False, None

        success, spectrum = yield read_and_average

        if success:
            self.noise.info.current_spectrum = spectrum
            self.plotSelectSpectrum()
            self.selected_spectrum_average.emit(spectrum)
            self.denoisePushButton.setEnabled(False)
        else:
            showInfo("failed")

    def plotSelectSpectrum(self):
        spectrum = self.noise.info.current_spectrum
        if spectrum is not None:
            self.plot.ax.plot(spectrum.mz, spectrum.intensity)
            self.plot.canvas.draw()

    @state_node
    def addFormula(self):
        formula = Formula(self.lineEdit.text())
        self.noise.info.general_setting.noise_formulas.append(
            workspace.noise_tab.NoiseFormulaParameter(formula=formula))
        self.showNoiseFormula()

    addFormula.except_node(showNoiseFormula)

    @state_node
    def delFormula(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        indexes.reverse()
        for index in indexes:
            del self.noise.info.general_setting.noise_formulas[index]
        self.showNoiseFormula()

    delFormula.except_node(showNoiseFormula)

    @state_node
    def calcNoise(self):
        info = self.noise.info
        spectrum = info.current_spectrum

        quantile = self.quantileDoubleSpinBox.value()
        n_sigma = self.nSigmaDoubleSpinBox.value()

        mass_dependent = self.sizeDependentCheckBox.isChecked()

        setting = info.general_setting
        mass_points = np.array([f.formula.mass()
                                for f in setting.noise_formulas])
        mass_point_deltas = np.array([self.tableWidget.cellWidget(
            i, 1).value() for i in range(self.tableWidget.rowCount())], dtype=np.int)

        def func():
            poly, std, slt, params = spectrum_func.getNoiseParams(
                spectrum.mz, spectrum.intensity, quantile, mass_dependent, mass_points, mass_point_deltas)
            noise, LOD = spectrum_func.noiseLODFunc(
                spectrum.mz, poly, params, mass_points, mass_point_deltas, n_sigma)
            return poly, std, slt, params, noise, LOD

        result = info.general_result

        result.poly_coef, result.global_noise_std, slt, params, result.noise, result.LOD = yield func

        setting = info.general_setting

        setting.params_inited = True
        setting.quantile, setting.mass_dependent, setting.n_sigma = quantile, mass_dependent, n_sigma

        ind: np.ndarray = slt.cumsum() - 1
        formula_params = setting.noise_formulas
        for index, (i, s, d) in enumerate(zip(ind, slt, mass_point_deltas)):
            p = formula_params[index]
            p.selected = p.useable = s
            if s:
                p.param = params[i]
            formula_params[index] = p
            p.delta = d

        self.showNoise()

    @state_node
    def reclacNoise(self):
        table = self.paramTableWidget
        checkeds, noises, lods = deque(), deque(), deque()

        for index in table.rowCount():
            checkbox: QtWidgets.QCheckBox = table.cellWidget(index, 0)
            checkeds.append(checkbox.isChecked())

            spinbox: QtWidgets.QDoubleSpinBox = table.cellWidget(index, 1)
            noises.append(spinbox.value())

            spinbox: QtWidgets.QDoubleSpinBox = table.cellWidget(index, 2)
            lods.append(spinbox.value())

        info = self.noise.info

        checkeds.popleft()
        result = info.general_result
        result.poly_coef, result.global_noise_std = spectrum_func.updateGlobalParam(
            result.poly_coef, info.general_setting.n_sigma, noises.popleft(), lods.popleft())

        for param, checked, noise, lod in zip(info.general_setting.noise_formulas, checkeds, noises, lods):
            param.param = spectrum_func.updateNoiseLODParam(
                param.param, info.general_setting.n_sigma, noise, lod)
            param.selected = checked

        self.showNoise()

    def showNoise(self):
        info = self.noise.info
        setting = info.general_setting
        result = info.general_result
        n_sigma = setting.n_sigma
        std = result.global_noise_std

        if not setting.params_inited:
            return
        global_noise, global_lod = spectrum_func.getGlobalShownNoise(
            result.poly_coef, n_sigma, std)

        useables = [True]
        checkeds = [True]
        names = ["global"]

        noises = [global_noise]
        lods = [global_lod]
        for param in info.general_setting.noise_formulas:
            useables.append(param.useable)
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

        for i, (useable, checked, name, noise, lod) in enumerate(zip(useables, checkeds, names, noises, lods)):
            checkBox = factory.CheckBoxFactory(checked)
            noisespinbox = factory.DoubleSpinBoxFactory(0, 1e11, 1, 1, noise)
            lodspinbox = factory.DoubleSpinBoxFactory(0, 1e11, 1, 1, lod)
            enable = i and useable
            checkBox.setEnabled(enable)
            noisespinbox.setEnabled(enable)
            lodspinbox.setEnabled(enable)

            table.setCellWidget(i, 0, checkBox)
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(name))
            table.setCellWidget(i, 2, noisespinbox)
            table.setCellWidget(i, 3, lodspinbox)

        self.toolBox.setCurrentWidget(self.paramTool)
        self.plotNoise()
        self.denoisePushButton.setEnabled(True)

    def plotNoise(self):
        info = self.noise.info
        spectrum = info.current_spectrum
        result = info.general_result

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

        ax.plot(spectrum.mz, spectrum.intensity,
                linewidth=1, color="#BF2138", label="Spectrum")
        ax.plot(spectrum.mz, result.LOD,
                linewidth=1, color='k', label='LOD')
        ax.plot(spectrum.mz, result.noise,
                linewidth=1, color='b', label='noise')
        ax.legend(loc='upper right')

        x_min = spectrum.mz[0]
        x_max = spectrum.mz[-1]
        ymax = np.polynomial.polynomial.polyval(
            x_max, result.poly_coef) + info.general_setting.n_sigma * result.global_noise_std
        if is_log:
            ymin = np.polynomial.polynomial.polyval(
                [x_min, x_max], result.poly_coef).min()
            ymin *= 0.5
            ymax *= 10
        else:
            ymin = 0
            ymax *= 5
        ax.set_ylim(ymin, ymax)
        plot.canvas.draw()

    @state_node
    def denoise(self):
        info = self.noise.info
        subtract = self.substractCheckBox.isChecked()
        spectrum = info.current_spectrum
        setting = info.general_setting

        def func():
            params, points, deltas = setting.get_params(True)
            mz, intensity = spectrum_func.denoiseWithParams(
                spectrum.mz, spectrum.intensity, info.general_result.poly_coef,
                params, points, deltas, setting.n_sigma, subtract)

            s = Spectrum(path=spectrum.path, mz=mz, intensity=intensity,
                         start_time=spectrum.start_time, end_time=spectrum.end_time)

            return s

        s = yield func

        read_from_file = ReadFromFile(self.manager.workspace)
        yield read_from_file

        setting.subtract = subtract
        setting.spectrum_dependent = self.dependentCheckBox.isChecked()

        self.callback.emit((s,))
