from copy import copy
import csv
from collections import deque
from datetime import datetime
from typing import Generator, Iterable, List, Optional, Tuple, Union

import matplotlib.ticker
import numpy as np
from numpy.polynomial.polynomial import polyval
from PyQt5 import QtCore, QtWidgets

from .. import workspace, setting
from ..functions import spectrum as spectrum_func, binary_search
from ..structures.file import FileSpectrumInfo
from ..structures.HDF5 import StructureListView, DiskListDirectView
from ..structures.spectrum import Spectrum
from ..utils.formula import Formula
from ..workspace import WorkSpace
from . import NoiseUi, component
from .component import factory
from .manager import Manager, MultiProcess, state_node
from .utils import (get_tablewidget_selected_row, savefile, set_header_sizes,
                    showInfo)


class Widget(QtWidgets.QWidget):
    selected_spectrum_average = QtCore.pyqtSignal(Spectrum)
    callback = QtCore.pyqtSignal(tuple)

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager

        self.ui = NoiseUi.Ui_Form()
        self.setupUi()

        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        set_header_sizes(ui.paramTableWidget.horizontalHeader(), [
                         100, 100, 150, 150])
        self.plot = component.Plot(ui.widget)
        ui.toolBox.setCurrentIndex(0)
        ui.showAveragePushButton.clicked.connect(self.showSelectedSpectrum)
        ui.addPushButton.clicked.connect(self.addFormula)
        ui.delPushButton.clicked.connect(self.delFormula)
        ui.calculateNoisePushButton.clicked.connect(self.calcNoise)
        ui.recalculateNoisePushButton.clicked.connect(self.reclacNoise)
        ui.exportDenoisedSpectrumPushButton.clicked.connect(
            self.exportDenoise)
        ui.exportNoisePeaksPushButton.clicked.connect(self.exportNoisePeaks)
        ui.denoisePushButton.clicked.connect(self.denoise)
        ui.skipPushButton.clicked.connect(self.skip)

        ui.paramTableWidget.itemDoubleClicked.connect(
            self.moveToTableClickedNoise)
        ui.spectrumPushButton.clicked.connect(self.scaleToSpectrum)
        ui.yLogCheckBox.toggled.connect(self.yLogToggle)
        ui.yAxisPushButton.clicked.connect(self.y_rescale_click)
        ui.yLimDoubleToolButton.clicked.connect(lambda: self.y_times(2))
        ui.yLimHalfToolButton.clicked.connect(lambda: self.y_times(.5))

    @property
    def info(self):
        return self.manager.workspace.info.noise_tab

    def restore(self):
        self.showNoiseFormula()
        self.plotSelectSpectrum()
        self.showNoise()
        self.info.ui_state.restore_state(self.ui)

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    def showNoiseFormula(self):
        widget = self.ui.tableWidget
        widget.clearContents()
        widget.setRowCount(0)
        formulas = self.info.general_setting.noise_formulas
        widget.setRowCount(len(formulas))
        for i, formula in enumerate(formulas):
            widget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                str(formula.formula)))
            dsb = QtWidgets.QSpinBox()
            dsb.setMinimum(1)
            dsb.setMaximum(50)
            dsb.setValue(int(formula.delta))
            widget.setCellWidget(i, 1, dsb)
            widget.setItem(i, 2, QtWidgets.QTableWidgetItem(
                format(formula.formula.mass(), ".6f")))

    @state_node
    def showSelectedSpectrum(self):
        yield from self.readSelectedSpectrum()
        self.ui.toolBox.setCurrentIndex(0)

    def readSelectedSpectrum(self):
        workspace = self.manager.workspace
        index = self.manager.getters.spectra_list_selected_index.get()
        info_list = workspace.info.file_tab.spectrum_infos

        left = index
        while left > 0 and info_list[left].average_index != 0:
            index -= 1
        right = index + 1
        while right < len(info_list) and info_list[right].average_index != 0:
            right += 1

        rtol = workspace.info.file_tab.rtol
        infos: List[FileSpectrumInfo] = list(info_list[left:right])

        def read_and_average():
            spectra: List[Tuple[np.ndarray, np.ndarray, float]] = []
            for info in infos:
                spectrum = info.get_spectrum_from_info(rtol, True)
                if spectrum is not None:
                    spectra.append(spectrum)
            if len(spectra) > 0:
                spectra = [(*spectrum_func.removeZeroPositions(
                    spectrum[0], spectrum[1]), spectrum[2]) for spectrum in spectra]
                mz, intensity = spectrum_func.averageSpectra(
                    spectra, rtol, True)
                spectrum = Spectrum('none:', mz, intensity,
                                    infos[0].start_time, infos[-1].end_time)
                return True, spectrum
            else:
                return False, None

        success, spectrum = yield read_and_average, "read & average"

        if success:
            self.info.current_spectrum = spectrum
            self.plotSelectSpectrum()
            self.selected_spectrum_average.emit(spectrum)
            self.ui.denoisePushButton.setEnabled(False)
        else:
            showInfo("failed")

    def plotSelectSpectrum(self):
        spectrum = self.info.current_spectrum
        if spectrum is not None:
            self.plot.ax.clear()
            self.plot.ax.plot(spectrum.mz, spectrum.intensity)
            self.plot.canvas.draw()
            self.y_rescale(self.ui.yLogCheckBox.isChecked())

    @state_node
    def addFormula(self):
        formula = Formula(self.ui.lineEdit.text())
        self.info.general_setting.noise_formulas.append(
            workspace.noise_tab.NoiseFormulaParameter(formula))
        self.showNoiseFormula()

    addFormula.except_node(showNoiseFormula)

    @state_node
    def delFormula(self):
        indexes = get_tablewidget_selected_row(self.ui.tableWidget)
        for index in reversed(indexes):
            del self.info.general_setting.noise_formulas[index]
        self.showNoiseFormula()

    delFormula.except_node(showNoiseFormula)

    @state_node
    def calcNoise(self):
        info = self.info
        spectrum = info.current_spectrum

        ui = self.ui
        quantile = ui.quantileDoubleSpinBox.value()
        n_sigma = ui.nSigmaDoubleSpinBox.value()

        mass_dependent = ui.sizeDependentCheckBox.isChecked()

        noise_setting = info.general_setting
        mass_points = np.array([f.formula.mass()
                                for f in noise_setting.noise_formulas])
        mass_point_deltas = np.array([ui.tableWidget.cellWidget(
            i, 1).value() for i in range(ui.tableWidget.rowCount())], dtype=np.int32)

        def func():
            poly, std, slt, params = spectrum_func.getNoiseParams(
                spectrum.mz, spectrum.intensity, quantile, mass_dependent, mass_points, mass_point_deltas)
            noise, LOD = spectrum_func.noiseLODFunc(
                spectrum.mz, poly, std, params, mass_points, mass_point_deltas, n_sigma)
            if setting.denoise.plot_noise_in_diff_color:
                noise_split = spectrum_func.splitNoise(
                    spectrum.mz, spectrum.intensity, poly, std, params,
                    mass_points, mass_point_deltas, n_sigma)
            else:
                noise_split = (None,) * 4

            return (poly, std, slt, params), (noise, LOD), noise_split

        result = info.general_result

        rets, noises, noise_split = yield func, "get noise infomations"

        result.poly_coef, result.global_noise_std, slt, params = rets
        result.noise, result.LOD = noises
        result.spectrum_mz, result.spectrum_intensity, result.noise_mz, result.noise_intensity = noise_split

        noise_setting = info.general_setting

        noise_setting.params_inited = True
        noise_setting.quantile, noise_setting.mass_dependent, noise_setting.n_sigma = quantile, mass_dependent, n_sigma

        ind: np.ndarray = slt.cumsum() - 1
        formula_params = noise_setting.noise_formulas
        for index, (i, s, d) in enumerate(zip(ind, slt, mass_point_deltas)):
            p = formula_params[index]
            p.selected = p.useable = s
            if s:
                p.param = params[i]
            p.delta = d

        self.showNoise()

    @state_node
    def reclacNoise(self):
        table = self.ui.paramTableWidget
        checkeds, noises, lods = deque(), deque(), deque()

        for index in range(table.rowCount()):
            checkbox: QtWidgets.QCheckBox = table.cellWidget(index, 0)
            checkeds.append(checkbox.isChecked())

            spinbox: QtWidgets.QDoubleSpinBox = table.cellWidget(index, 2)
            noises.append(spinbox.value())

            spinbox: QtWidgets.QDoubleSpinBox = table.cellWidget(index, 3)
            lods.append(spinbox.value())

        info = self.info

        checkeds.popleft()
        result = info.general_result
        result.poly_coef, result.global_noise_std = spectrum_func.updateGlobalParam(
            result.poly_coef, info.general_setting.n_sigma, noises.popleft(), lods.popleft())

        for param, checked, noise, lod in zip(info.general_setting.noise_formulas, checkeds, noises, lods):
            if param.useable:
                param.param = spectrum_func.updateNoiseLODParam(
                    param.param, info.general_setting.n_sigma, noise, lod)
                param.selected = checked

        noise_setting = info.general_setting
        spectrum = info.current_spectrum
        result.spectrum_mz, result.spectrum_intensity, result.noise_mz, result.noise_intensity = noise_split

        def func():
            params, points, deltas = noise_setting.get_params()
            noise, LOD = spectrum_func.noiseLODFunc(
                spectrum.mz, result.poly_coef, result.global_noise_std,
                params, points, deltas, noise_setting.n_sigma)
            if setting.denoise.plot_noise_in_diff_color:
                noise_split = spectrum_func.splitNoise(
                    spectrum.mz, spectrum.intensity, result.poly_coef, result.global_noise_std,
                    params, points, deltas, noise_setting.n_sigma)
            else:
                noise_split = (None,) * 4
            return noise, LOD, noise_split
        result.noise, result.LOD, noise_split = yield func, "recalc noise"

        self.showNoise()

    def showNoise(self):
        ui = self.ui
        info = self.info
        noise_setting = info.general_setting
        result = info.general_result
        n_sigma = noise_setting.n_sigma
        std = result.global_noise_std

        if not noise_setting.params_inited:
            return
        global_noise, global_lod = spectrum_func.getGlobalShownNoise(
            result.poly_coef, n_sigma, std)

        useables = [True]
        checkeds = [True]
        names = ["global"]

        noises = [global_noise]
        lods = [global_lod]
        for param in noise_setting.noise_formulas:
            useables.append(param.useable)
            checkeds.append(param.selected)
            names.append(str(param.formula))
            if param.useable:
                noise, lod = spectrum_func.getNoiseLODFromParam(
                    param.param, n_sigma)
                noises.append(noise)
                lods.append(lod)
            else:
                noises.append(0)
                lods.append(0)

        table = ui.paramTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(checkeds))

        for i, (useable, checked, name, noise, lod) in enumerate(zip(useables, checkeds, names, noises, lods)):
            checkBox = factory.CheckBox(checked)
            noisespinbox = factory.DoubleSpinBox(-1e10, 1e11, 1, 1, noise)
            lodspinbox = factory.DoubleSpinBox(-1e10, 1e11, 1, 1, lod)
            checkBox.setEnabled(useable and i)
            noisespinbox.setEnabled(useable)
            lodspinbox.setEnabled(useable)

            table.setCellWidget(i, 0, checkBox)
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(name))
            table.setCellWidget(i, 2, noisespinbox)
            table.setCellWidget(i, 3, lodspinbox)

        ui.toolBox.setCurrentWidget(ui.paramTool)
        self.plotNoise()
        ui.denoisePushButton.setEnabled(True)

    def plotNoise(self):
        info = self.info
        spectrum = info.current_spectrum
        if spectrum is None:
            return
        result = info.general_result

        is_log = self.ui.yLogCheckBox.isChecked()
        plot = self.plot
        ax = plot.ax
        ax.clear()

        ax.set_yscale('log' if is_log else 'linear')

        ax.axhline(color='k', linewidth=0.5)
        ax.yaxis.set_tick_params(rotation=45)

        if not is_log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.plot(spectrum.mz, result.LOD,
                linewidth=1, color='k', label='LOD')
        ax.plot(spectrum.mz, result.noise,
                linewidth=1, color='b', label='noise')
        if setting.denoise.plot_noise_in_diff_color and result.spectrum_mz is not None:
            ax.plot(result.spectrum_mz, result.spectrum_intensity,
                    linewidth=1, color="#1f77b4", label="Spectrum")
            ax.plot(result.noise_mz, result.noise_intensity,
                    linewidth=1, color="#BF2138", label="Noise")
        else:
            ax.plot(spectrum.mz, spectrum.intensity,
                    linewidth=1, color="#BF2138", label="Spectrum")
        ax.legend(loc='upper right')

        self.moveToGlobalNoise()
        plot.canvas.draw()

    @state_node
    def exportDenoise(self):
        info = self.info
        subtract = self.ui.substractCheckBox.isChecked()
        spectrum = info.current_spectrum
        noise_setting = info.general_setting

        ret, f = savefile("Save Denoise Spectrum", "CSV file(*.csv)",
                          f"denoise_spectrum {spectrum.start_time.strftime(setting.general.export_time_format)}"
                          f"-{spectrum.end_time.strftime(setting.general.export_time_format)}.csv")
        if not ret:
            return

        def func():
            params, points, deltas = noise_setting.get_params(True)
            mz, intensity = spectrum_func.denoiseWithParams(
                spectrum.mz, spectrum.intensity, info.general_result.poly_coef,
                info.general_result.global_noise_std, params, points, deltas,
                noise_setting.n_sigma, subtract)

            s = Spectrum(spectrum.path, mz, intensity,
                         spectrum.start_time, spectrum.end_time)

            return s

        s: Spectrum = yield func, "doing denoise"

        def export():
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["mz", "intensity"])
                writer.writerows(self.manager.tqdm(
                    zip(s.mz, s.intensity), length=len(s.mz)))

        yield export, "export"

    @state_node
    def exportNoisePeaks(self):
        info = self.info
        spectrum = info.current_spectrum
        noise_setting = info.general_setting
        ret, f = savefile("Save Noise Peak", "CSV file(*.csv)",
                          f"noise_peak {spectrum.start_time.strftime(setting.general.export_time_format)}"
                          f"-{spectrum.end_time.strftime(setting.general.export_time_format)}.csv")
        if not ret:
            return

        def func():
            params, points, deltas = noise_setting.get_params(True)
            mz, intensity = spectrum_func.getNoisePeaks(
                spectrum.mz, spectrum.intensity, info.general_result.poly_coef,
                info.general_result.global_noise_std, params, points, deltas, noise_setting.n_sigma)
            return mz, intensity

        mz, intensity = yield func, "get noise peak"

        def export():
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["peak position", "peak intensity"])
                writer.writerows(self.manager.tqdm(
                    zip(mz, intensity), length=len(mz)))
        yield export, "export"

    @state_node
    def denoise(self):
        info = self.info
        subtract = self.ui.substractCheckBox.isChecked()
        spectrum = info.current_spectrum
        noise_setting = info.general_setting

        def func():
            params, points, deltas = noise_setting.get_params(True)
            mz, intensity = spectrum_func.denoiseWithParams(
                spectrum.mz, spectrum.intensity, info.general_result.poly_coef,
                info.general_result.global_noise_std, params, points, deltas,
                noise_setting.n_sigma, subtract)

            s = Spectrum(spectrum.path, mz, intensity,
                         spectrum.start_time, spectrum.end_time)

            return s

        s = yield func, "doing denoise"

        read_from_file = ReadFromFile(self.manager.workspace)
        yield read_from_file, "read and average all spectra"

        noise_setting.subtract = subtract
        noise_setting.spectrum_dependent = self.ui.dependentCheckBox.isChecked()
        info.skip = False

        self.callback.emit((s,))

    @state_node
    def skip(self):
        yield ReadFromFile(self.manager.workspace), "read and average all spectra"
        info = self.info
        info.skip = True
        if info.current_spectrum is None:
            yield from self.readSelectedSpectrum()
        self.callback.emit((info.current_spectrum,))

    @state_node(withArgs=True)
    def moveToTableClickedNoise(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        info = self.info
        if info.current_spectrum is None:
            return
        if not info.general_setting.params_inited:
            return

        noise_setting = info.general_setting
        result = info.general_result

        plot = self.plot
        if row == 0:  # noise
            self.moveToGlobalNoise()
        else:
            param = noise_setting.noise_formulas[row - 1]

            point = param.formula.mass()
            x_min = point - param.delta * 2
            x_max = point + param.delta * 2
            xrange = [x_min, x_max]
            global_range = polyval(xrange, result.poly_coef)
            if param.useable:
                y_min = global_range.min()
                _, y_max = spectrum_func.getNoiseLODFromParam(
                    param.param, noise_setting.n_sigma)
            else:  # global noise
                y_min = global_range.min()
                y_max = global_range.max() + noise_setting.n_sigma * result.global_noise_std

            plot.ax.set_xlim(x_min, x_max)
            plot.ax.set_ylim(y_min, y_max)
        plot.canvas.draw()

    def moveToGlobalNoise(self):
        ui = self.ui
        is_log = ui.yLogCheckBox.isChecked()
        ax = self.plot.ax

        info = self.info
        spectrum = info.current_spectrum
        result = info.general_result

        x_min = spectrum.mz[0]
        x_max = spectrum.mz[-1]
        yrange = polyval([x_min, x_max], result.poly_coef)
        y_min = yrange.min()
        y_max = abs(yrange.max() + info.general_setting.n_sigma *
                    result.global_noise_std)
        if is_log:
            if y_min > 0:
                y_min *= 0.5
            else:
                y_min = 0
            y_max *= 10
        else:
            if y_min > 0:
                y_min = 0
            else:
                y_min *= 2

            y_max *= 5
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

    @state_node
    def scaleToSpectrum(self):
        info = self.info
        if info.current_spectrum is None:
            return

        is_log = self.ui.yLogCheckBox.isChecked()

        spectrum = info.current_spectrum
        self.plot.ax.set_xlim(spectrum.mz.min(), spectrum.mz.max())

        self.y_rescale(is_log)

        self.plot.canvas.draw()

    @state_node(withArgs=True)
    def yLogToggle(self, is_log: bool):
        ax = self.plot.ax
        ax.set_yscale('log' if is_log else 'linear')

        if not is_log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        if self.info.current_spectrum is None:
            return

        self.y_rescale(is_log)
        self.plot.canvas.draw()

    @state_node
    def y_rescale_click(self):
        is_log = self.ui.yLogCheckBox.isChecked()
        self.y_rescale(is_log)
        self.plot.canvas.draw()

    def y_rescale(self, is_log: bool):
        plot = self.plot
        ax = plot.ax
        spectrum = self.info.current_spectrum

        x_min, x_max = ax.get_xlim()
        id_x_min, id_x_max = binary_search.indexBetween_np(
            spectrum.mz, (x_min, x_max))

        y_max = spectrum.intensity[id_x_min:id_x_max].max()

        if is_log:
            info = self.info
            if info.general_setting.params_inited:
                y_min = polyval(
                    [x_min, x_max], info.general_result.poly_coef).min() / 10
            else:
                y_min = 0.1
            y_max *= 2
        else:
            dy = 0.05 * y_max
            y_min = -dy
            y_max = y_max + dy

        ax.set_ylim(y_min, y_max)

    @state_node(withArgs=True)
    def y_times(self, times: float):
        plot = self.plot
        ax = plot.ax
        y_min, y_max = ax.get_ylim()
        y_max *= times
        if not self.ui.yLogCheckBox.isChecked():
            y_min = - 0.025 * y_max
        ax.set_ylim(y_min, y_max)
        plot.canvas.draw()


class ReadFromFile(MultiProcess):
    @staticmethod
    def func(data: Tuple[FileSpectrumInfo, Tuple[np.ndarray, np.ndarray, float]], **kwargs):
        info, (mz, intensity) = data
        mz, intensity = spectrum_func.removeZeroPositions(mz, intensity)
        spectrum = Spectrum(info.path, mz, intensity,
                            info.start_time, info.end_time)
        return info, spectrum

    @staticmethod
    def read(file: WorkSpace, **kwargs) -> Generator:
        rtol = file.info.file_tab.rtol
        cnt = 0
        for info in file.info.file_tab.spectrum_infos:
            data = info.get_spectrum_from_info(rtol)
            if info.average_index and info.average_index != cnt:
                info = copy(info)
                info.average_index = cnt
            if data is not None:
                yield info, data
                cnt = info.average_index + 1
            else:
                cnt = info.average_index

    @staticmethod
    def read_len(file: WorkSpace, **kwargs) -> int:
        return len(file.info.file_tab.spectrum_infos)

    @staticmethod
    def write(file: WorkSpace, rets: Iterable[Tuple[FileSpectrumInfo, Spectrum]], **kwargs):
        obj = (file.proxy_file or file.file)._obj
        tmp = DiskListDirectView[Spectrum](obj, "tmp")
        infos = []

        def it():
            for info, spectrum in rets:
                infos.append(info)
                yield spectrum
        tmp.extend(it())

        file.info.noise_tab.denoised_spectrum_infos = infos
        file.info.noise_tab.to_be_calibrate = True
        path = file.data.raw_spectra.obj.name
        del obj[path]
        obj.move(tmp.obj.name, path)

    @staticmethod
    def exception(file: WorkSpace, **kwargs):
        obj = (file.proxy_file or file.file)._obj
        if "tmp" in obj:
            del file["tmp"]
