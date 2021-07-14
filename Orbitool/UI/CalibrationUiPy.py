from datetime import datetime
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

import numpy as np
from PyQt5 import QtCore, QtWidgets
import matplotlib.ticker

from ..functions import spectrum as spectrum_func
from ..functions.calibration import Calibrator, PolynomialRegressionFunc
from ..functions.peakfit.normal_distribution import NormalDistributionFunc
from ..structures.file import FileSpectrumInfo
from ..structures.HDF5 import StructureConverter, StructureListView
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..workspace import WorkSpace
from . import CalibrationUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row


class Widget(QtWidgets.QWidget, CalibrationUi.Ui_Form):
    calcInfoFinished = QtCore.pyqtSignal()
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.setupUi(self)
        manager.inited_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = Plot(self.widget)

        self.addIonToolButton.clicked.connect(self.addIon)
        self.delIonToolButton.clicked.connect(self.removeIon)
        self.calcInfoPushButton.clicked.connect(self.calcInfo)
        self.finishPushButton.clicked.connect(self.calibrate)

        self.showSpectrumPushButton.clicked.connect(self.showSpectrum)
        self.showSelectedPushButton.clicked.connect(self.showSelected)
        self.showAllPushButton.clicked.connect(self.showAllInfoClicked)

    @ property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def restore(self):
        self.showIons()
        self.calibration.ui_state.set_state(self)

    def updateState(self):
        self.calibration.ui_state.fromComponents(self, [
            self.rtolDoubleSpinBox,
            self.degreeSpinBox,
            self.nIonsSpinBox])

    def showIons(self):
        info = self.calibration.info
        table = self.tableWidget
        table.clearContents()
        table.setRowCount(len(info.ions))
        for index, ion in enumerate(info.ions):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ion.shown_text))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(format(ion.formula.mass(), ".4f")))

    @ state_node
    def addIon(self):
        self.calibration.info.add_ions(self.ionLineEdit.text().split(','))
        self.showIons()

    @ state_node
    def removeIon(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        ions = self.calibration.info.ions
        for index in reversed(indexes):
            ions.pop(index)
        self.showIons()

    @ state_node
    def calcInfo(self):
        workspace = self.manager.workspace
        calibration_tab = self.calibration
        info = calibration_tab.info

        intensity_filter = 100
        rtol = self.rtolDoubleSpinBox.value() / 1e-6
        degree = self.degreeSpinBox.value()
        use_N_ions = self.nIonsSpinBox.value()

        raw_spectra = workspace.file_tab.raw_spectra
        fit_func = workspace.peak_shape_tab.info.func

        # use ions to decide whether to split
        need_to_split = True
        if len(info.calibrators) > 0:
            calculator = next(iter(info.calibrators.values()))
            calculated_ions = {ion.formula for ion in calculator.ions}
            now_ions = {ion.formula for ion in info.ions}
            if now_ions == calculated_ions:
                need_to_split = False

        if need_to_split:  # read ions from spectrum
            path_time = {
                path.path: path.createDatetime for path in workspace.file_tab.info.pathlist}
            ions = [ion.formula.mass() for ion in info.ions]
            split_and_fit = SplitAndFitPeak(
                raw_spectra,
                func_kwargs=dict(
                    fit_func=fit_func, ions=ions, intensity_filter=intensity_filter))

            path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = yield split_and_fit, "split and fit target peaks"
            # file path -> info of a file
            # shape : len(spectrum of file), len(ions), 2 # position, intensity

            def get_calibrator():
                path_calibrators: Dict[str, Calibrator] = {}

                for path, ions_peak in path_ions_peak.items():
                    ions_peak = np.array(ions_peak, dtype=float)
                    ions_position = ions_peak[:, :, 0]
                    ions_intensity = ions_peak[:, :, 1]
                    path_calibrators[path] = Calibrator.FactoryFromMzInt(
                        path_time[path], info.ions, ions_position, ions_intensity, rtol, use_N_ions)

                return path_calibrators

            info.calibrators = yield get_calibrator, "calculate calibrator"
        else:  # get info directly
            def get_calibrator_from_calibrator():
                return {path: calibrator.regeneratCalibrator(rtol=rtol, use_N_ions=use_N_ions) for path, calibrator in info.calibrators.items()}

            info.calibrators = yield get_calibrator_from_calibrator, "generate calibrator from former calibrator"

        def generate_func_from_calibrator():
            ret = {}
            for path, calibrator in info.calibrators.items():
                min_index = calibrator.min_indexes
                func = PolynomialRegressionFunc.FactoryFit(
                    calibrator.ions_position[min_index], calibrator.ions_rtol[min_index], degree)
                ret[path] = func
            return ret
        info.poly_funcs = yield generate_func_from_calibrator, "calculate function from calibrator"

        self.calcInfoFinished.emit()

    @state_node
    def showSpectrum(self):
        index = self.manager.fetch_func("spectra list select")()
        workspace = self.manager.workspace
        spectrum = workspace.file_tab.raw_spectra[index]
        calibrator = self.calibration.info.calibrators[spectrum.path]
        inner_index = index
        for cal in self.calibration.info.calibrators.values():
            if index < len(cal.ions_raw_position):
                break
            inner_index -= len(cal.ions_raw_position)

        ions_position = calibrator.ions_raw_position[inner_index]
        ions_intensity = calibrator.ions_raw_intensity[inner_index]

        table = self.manager.calibrationInfoWidget

        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)

        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["mz", "rtol", "intensity"])
        table.setVerticalHeaderLabels(
            [ion.shown_text for ion in calibrator.ions])

        table.setRowCount(len(calibrator.ions))

        for index, (ion, mz, intensity) in enumerate(zip(calibrator.ions, ions_position, ions_intensity)):
            table.setItem(
                index, 0, QtWidgets.QTableWidgetItem(format(mz, '.5f')))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(
                    format(abs(1 - ion.formula.mass() / mz) * 1e6, '.5f')))
            table.setItem(
                index, 2, QtWidgets.QTableWidgetItem(
                    format(intensity, '.3e')))

        plot = self.plot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        ax.plot(spectrum.mz, spectrum.intensity, color='black')

        for x, y in zip(ions_position, ions_intensity):
            ax.plot([x, x], [0, y], color='red')
        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.relim()
        ax.autoscale_view(True, True, True)
        plot.canvas.draw()

    @state_node
    def showSelected(self):
        index = self.manager.fetch_func("calibration info selected index")()

        table = self.manager.calibrationInfoWidget
        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)

        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            ['theoretic mz', 'mz', 'ppm', 'use for calibration'])

        calibrator = list(self.calibration.info.calibrators.values())[index]
        func = list(self.calibration.info.poly_funcs.values())[index]

        table.setRowCount(len(calibrator.ions_position))
        table.setVerticalHeaderLabels(
            [ion.shown_text for ion in calibrator.ions])
        for i in range(len(calibrator.ions_position)):
            def setValue(column, s):
                table.setItem(i, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, format(calibrator.ions[i].formula.mass(), '.5f'))
            setValue(1, format(calibrator.ions_position[i], '.5f'))
            setValue(2, format(calibrator.ions_rtol[i] * 1e6, '.5f'))
            setValue(3, 'True' if i in calibrator.min_indexes else 'False')

        formula_info = self.manager.workspace.formula_docker.info

        x = np.linspace(formula_info.mz_min, formula_info.mz_max, 1000)
        xx = func.predictRtol(x) * 1e6
        plot = self.plot
        ax = plot.ax
        ax.clear()

        ax.axhline(color='black', linewidth=0.5)
        ax.plot(x, xx)

        ions_position = calibrator.ions_position
        ions_rtol = calibrator.ions_rtol
        min_index = calibrator.min_indexes
        max_index = calibrator.max_indexes
        x = ions_position[min_index]
        y = ions_rtol[min_index] * 1e6
        ax.scatter(x, y, c='black')
        x = ions_position[max_index]
        y = ions_rtol[max_index] * 1e6
        ax.scatter(x, y, c='red')

        ax.set_ylabel('ppm')
        ax.set_xlim(formula_info.mz_min, formula_info.mz_max)
        plot.canvas.draw()

    @state_node
    def showAllInfoClicked(self):
        self.showAllInfo()

    def showAllInfo(self):
        table = self.manager.calibrationInfoWidget
        table.clearContents()

        info = self.calibration.info

        table.setColumnCount(len(info.ions))
        hlables = [ion.shown_text for ion in info.ions]
        table.setHorizontalHeaderLabels(hlables)

        table.setRowCount(len(info.calibrators))
        if len(info.calibrators) == 0:
            return

        calibrators = sorted(info.calibrators.values(),
                             key=lambda calibrator: calibrator.time)

        times = []
        devitions = []
        for row, calibrator in enumerate(calibrators):
            times.append(calibrator.time)

            for column, rtol in enumerate(calibrator.ions_rtol):
                table.setItem(row, column, QtWidgets.QTableWidgetItem(
                    format(rtol * 1e6, ".5f")))
            devitions.append(calibrator.ions_rtol)
        vlabels = [time.replace(microsecond=0).isoformat(
            sep=' ')[:-3] for time in times]

        table.setVerticalHeaderLabels(vlabels)

        devitions = np.array(devitions)

        plot = self.plot

        ax = plot.ax
        ax.clear()
        ax.axhline(color="k", linewidth=.5)

        if len(devitions) > 0:
            for index in range(devitions.shape[1]):
                ax.plot(times, devitions[:, index],
                        label=info.ions[index].shown_text)

        ax.set_xlabel("starting time")
        ax.set_ylabel("Deviation (ppm)")
        ax.legend()
        ax.relim()
        ax.autoscale(True, True, True)
        plot.canvas.draw()

    @state_node
    def calibrate(self):
        workspace = self.manager.workspace
        noise_info = workspace.noise_tab.info
        setting = noise_info.general_setting
        result = noise_info.general_result
        dependent = setting.mass_dependent
        params, points, deltas = setting.get_params(not dependent)
        func_kwargs = {
            "quantile": setting.quantile,
            "mass_dependent": setting.mass_dependent,
            "n_sigma": setting.n_sigma,
            "dependent": dependent,
            "points": points,
            "deltas": deltas,
            "params": params,
            "subtract": setting.subtract,
            "poly_coef": result.poly_coef}
        calibrate_merge = CalibrateMergeDenoise(
            self.manager.workspace, func_kwargs=func_kwargs)
        yield calibrate_merge, "calibrate"
        self.callback.emit()


class SplitAndFitPeak(MultiProcess):
    @staticmethod
    def read(h5_spectra: StructureListView[Spectrum], **kwargs) -> Generator:
        return h5_spectra

    @staticmethod
    def read_len(h5_spectra: StructureListView[Spectrum], **kwargs) -> int:
        return len(h5_spectra)

    @staticmethod
    def func(data: Spectrum, fit_func: NormalDistributionFunc, ions: List[float], intensity_filter: float, **kwargs):
        ions_peak: List[Tuple[float, float]] = []
        for ion in ions:
            peak = fit_func.fetchNearestPeak(
                data, ion, intensity_filter)
            ions_peak.append(
                (peak.peak_position, peak.peak_intensity))

        return data.path, ions_peak

    @staticmethod
    def write(file, rets, **kwargs):
        path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = {}
        for path, ions_peak in rets:
            path_ions_peak.setdefault(path, []).append(ions_peak)
        return path_ions_peak

    @staticmethod
    def exception(file, **kwargs):
        pass


class CalibrateMergeDenoise(MultiProcess):
    @staticmethod
    def read(file: WorkSpace, **kwargs) -> Generator[List[Tuple[Spectrum, PolynomialRegressionFunc]], Any, Any]:
        batch = []
        file_tab = file.file_tab
        funcs = file.calibration_tab.info.poly_funcs
        for info, spectrum in zip(file_tab.info.spectrum_infos, file_tab.raw_spectra):
            if info.average_index > 0:
                batch.append((spectrum, funcs[spectrum.path]))
            else:
                if batch:
                    yield batch
                batch = [(spectrum, funcs[spectrum.path])]
        yield batch

    @staticmethod
    def read_len(file: WorkSpace, **read_kwargs) -> int:
        cnt = 0
        for info in file.file_tab.info.spectrum_infos:
            if info.average_index == 0:
                cnt += 1
        return cnt

    @staticmethod
    def func(data: List[Tuple[Spectrum, PolynomialRegressionFunc]],
             quantile: float, mass_dependent: bool, n_sigma: bool,
             dependent: bool, points: np.ndarray, deltas: np.ndarray,
             params: np.ndarray, subtract: bool, poly_coef: np.ndarray) -> Spectrum:
        spectra = []
        paths = set()
        start_times = []
        end_times = []
        for spectrum, func in data:
            spectrum.mz = func.predictMz(spectrum.mz)
            spectra.append((spectrum.mz, spectrum.intensity,
                            (spectrum.end_time - spectrum.start_time).total_seconds()))
            paths.add(spectrum.path)
            start_times.append(spectrum.start_time)
            end_times.append(spectrum.end_time)

        path = paths.pop() if len(paths) == 1 else ""
        mz, intensity = spectrum_func.averageSpectra(spectra, drop_input=True)

        if not dependent:
            poly_coef, _, slt, params = spectrum_func.getNoiseParams(
                mz, intensity, quantile, mass_dependent, points, deltas)
            points = points[slt]
            deltas = deltas[slt]

        mz, intensity = spectrum_func.denoiseWithParams(
            mz, intensity, poly_coef, params, points, deltas, n_sigma, subtract)

        start_time = min(start_times)
        end_time = max(end_times)
        spectrum = Spectrum(path=path, mz=mz, intensity=intensity,
                            start_time=start_time, end_time=end_time)
        return spectrum

    @staticmethod
    def write(file: WorkSpace, rets: Iterable[Spectrum], **kwargs):
        tmp = StructureListView[Spectrum](file._obj, "tmp", True)
        infos = file.calibration_tab.info.calibrated_spectrum_infos
        infos.clear()
        for ret in rets:
            tmp.h5_append(ret)
            infos.append(SpectrumInfo(
                start_time=ret.start_time, end_time=ret.end_time))

        target = file.calibration_tab.calibrated_spectra
        path = target.h5_path
        if path in file:
            del file._obj[path]
        file._obj.move(tmp.h5_path, path)

    @staticmethod
    def exception(file, **kwargs):
        if "tmp" in file:
            del file["tmp"]
