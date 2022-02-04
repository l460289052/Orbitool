from functools import partial
import math
from enum import Enum
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union
from itertools import chain

import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.ticker

from ..functions import spectrum as spectrum_func, binary_search, peakfit as peakfit_func
from ..functions.calibration import Calibrator, PolynomialRegressionFunc
from ..functions.peakfit.normal_distribution import NormalDistributionFunc
from ..structures.HDF5 import StructureListView
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..workspace import WorkSpace
from . import CalibrationUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row, showInfo


class ShownState(int, Enum):
    all_info = 0
    spectrum = 1
    file = 2


class Widget(QtWidgets.QWidget, CalibrationUi.Ui_Form):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.setupUi(self)
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

        self.spectrum_inner_index: int = None
        self.spectrum_current_ion_index: int = None
        self.shown_state: ShownState = ShownState.all_info

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = Plot(self.widget)

        self.separatorListWidget.itemDoubleClicked.connect(self.changeSegment)
        self.separatorListWidget.mouseReleaseEvent = self.mouseRelease
        self.separatorAddPushButton.clicked.connect(self.addSegment)

        self.addIonToolButton.clicked.connect(self.addIon)
        self.delIonToolButton.clicked.connect(self.removeIon)
        self.calcInfoPushButton.clicked.connect(self.calcInfo)
        self.finishPushButton.clicked.connect(
            lambda: self.calibrate(skip=False))
        self.skipPushButton.clicked.connect(lambda: self.calibrate(skip=True))

        self.previousIonsShortCut = QtWidgets.QShortcut("Left", self)
        self.previousIonsShortCut.activated.connect(lambda: self.next_ion(-1))
        self.nextIonShortCut = QtWidgets.QShortcut("Right", self)
        self.nextIonShortCut.activated.connect(lambda: self.next_ion(1))

    @property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def restore(self):
        self.showSegments()
        self.showCurrentSegment()
        self.calibration.ui_state.set_state(self)

    def updateState(self):
        self.calibration.ui_state.fromComponents(self, [
            self.rtolDoubleSpinBox,
            self.degreeSpinBox,
            self.nIonsSpinBox])

    def showSegments(self):
        workspace = self.manager.workspace
        begin_point = workspace.formula_docker.info.mz_min
        end_point = workspace.formula_docker.info.mz_max

        listwidget = self.separatorListWidget
        listwidget.clear()
        points = [
            seg.end_point for seg in self.calibration.info.calibrator_segments]
        points.pop()
        for begin, end in zip([begin_point, *points], [*points, end_point]):
            listwidget.addItem("{:.2f}-{:.2f}".format(begin, end))

    def showCurrentSegment(self):
        info = self.calibration.info
        ind = info.current_segment_index
        self.separatorListWidget.setCurrentRow(ind)
        seg = info.calibrator_segments[ind]
        table = self.tableWidget
        table.clearContents()
        table.setRowCount(len(seg.ions))
        for index, ion in enumerate(seg.ions):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ion.shown_text))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(format(ion.formula.mass(), ".4f")))

        self.rtolDoubleSpinBox.setValue(seg.rtol * 1e6)
        self.degreeSpinBox.setValue(seg.degree)
        self.nIonsSpinBox.setValue(seg.n_ions)

    def saveCurrentSegment(self):
        info = self.calibration.info
        seg = info.calibrator_segments[info.current_segment_index]
        seg.rtol = self.rtolDoubleSpinBox.value() * 1e-6
        seg.degree = self.degreeSpinBox.value()
        seg.n_ions = self.nIonsSpinBox.value()

    @state_node
    def addSegment(self):
        separator = self.separatorDoubleSpinBox.value()
        formula_info = self.manager.workspace.formula_docker.info
        assert formula_info.mz_min < separator < formula_info.mz_max, "please check mz range in formula docker"
        self.calibration.info.add_segment(separator)
        self.showSegments()
        self.showCurrentSegment()

    @state_node(mode='n', withArgs=True)
    def mouseRelease(self, e: QtGui.QMouseEvent):
        indexes = [ind.row()
                   for ind in self.separatorListWidget.selectedIndexes()]
        if len(indexes) > 1:
            menu = QtWidgets.QMenu(self)

            merge = QtWidgets.QAction('merge', menu)

            func = partial(self.mergeSegment, indexes)
            merge.triggered.connect(lambda: func())
            menu.addAction(merge)
            menu.popup(e.globalPos())
        return QtWidgets.QListWidget.mouseReleaseEvent(self.separatorListWidget, e)

    @state_node(withArgs=True)
    def mergeSegment(self, indexes: List[int]):
        ma = max(indexes)
        mi = min(indexes)
        assert ma - mi == len(indexes) - \
            1, "cannot merge unjoined segments"
        info = self.calibration.info
        info.merge_segment(mi, ma + 1)
        if mi < info.current_segment_index:
            if info.current_segment_index <= ma:
                info.current_segment_index = mi
            else:
                info.current_segment_index -= ma - mi

        self.showSegments()
        self.showCurrentSegment()

    @state_node(withArgs=True)
    def changeSegment(self, item: QtWidgets.QListWidgetItem):
        # save

        ind = self.separatorListWidget.row(item)
        self.calibration.info.current_segment_index = ind

        self.showCurrentSegment()

    @state_node
    def addIon(self):
        # check range
        self.calibration.info.add_ions(self.ionLineEdit.text().split(','))
        self.showCurrentSegment()

    @state_node
    def removeIon(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        ions = self.calibration.info.ions
        for index in reversed(indexes):
            ions.pop(index)
        self.showCurrentSegment()

    @state_node
    def calcInfo(self):
        workspace = self.manager.workspace
        calibration_tab = self.calibration
        info = calibration_tab.info

        intensity_filter = 100
        self.saveCurrentSegment()

        # 需要为每个校准器都使用以下的步骤！
        rtol = self.rtolDoubleSpinBox.value() * 1e-6
        degree = self.degreeSpinBox.value()
        use_N_ions = self.nIonsSpinBox.value()

        raw_spectra = workspace.file_tab.raw_spectra
        fit_func = workspace.peak_shape_tab.info.func

        # use ions to decide whether to split
        need_to_split = True
        if abs(info.rtol / rtol - 1) < 1e-6 and len(info.calibrators) > 0:
            calculator = next(iter(info.calibrators.values()))
            calculated_ions = {ion.formula for ion in calculator.ions}
            now_ions = {ion.formula for ion in info.ions}
            if now_ions == calculated_ions:
                need_to_split = False

            for spectrum_info in workspace.file_tab.info.spectrum_infos:
                if spectrum_info.path not in info.calibrators:
                    need_to_split = True
                    break
        info.rtol = rtol

        if need_to_split:  # read ions from spectrum
            path_time = {
                path.path: path.createDatetime for path in workspace.file_tab.info.pathlist}
            ions = [ion.formula.mass() for ion in info.ions]
            split_and_fit = SplitAndFitPeak(
                raw_spectra,
                func_kwargs=dict(
                    fit_func=fit_func, ions=ions, intensity_filter=intensity_filter, rtol=rtol))

            path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = yield split_and_fit, "split and fit target peaks"
            # file path -> info of a file
            # shape : len(spectrum of file), len(ions), 2 # position, intensity

            def get_calibrator():
                path_calibrators: Dict[str, Calibrator] = {}

                for path, ions_peak in path_ions_peak.items():
                    ions_peak = np.array(ions_peak, dtype=float)
                    ions_position = ions_peak[:, :, 0]
                    ions_intensity = ions_peak[:, :, 1]
                    path_calibrators[path] = Calibrator.fromMzInt(
                        path_time[path], info.ions, ions_position, ions_intensity, rtol, use_N_ions)

                return path_calibrators

            info.calibrators = yield get_calibrator, "calculate calibrator"
        else:  # get info directly
            def get_calibrator_from_calibrator():
                return {path: calibrator.regeneratCalibrator(rtol, use_N_ions) for path, calibrator in info.calibrators.items()}

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

        self.showAllInfo()

    @state_node
    def showSpectrum(self):
        index = self.manager.getters.spectra_list_selected_index.get()
        workspace = self.manager.workspace
        spectrum = workspace.file_tab.raw_spectra[index]
        calibrator = self.calibration.info.calibrators[spectrum.path]
        inner_index = index
        for cal in self.calibration.info.calibrators.values():
            if index < len(cal.ions_raw_position):
                break
            inner_index -= len(cal.ions_raw_position)

        self.spectrum_inner_index = inner_index
        ions_position = calibrator.ions_raw_position[inner_index]
        ions_intensity = calibrator.ions_raw_intensity[inner_index]

        table = self.manager.calibrationInfoWidget

        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)

        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["mz", "rtol", "intensity"])

        table.setRowCount(len(calibrator.ions))
        table.setVerticalHeaderLabels(
            [ion.shown_text for ion in calibrator.ions])

        min_indexes = set(calibrator.min_indexes)
        color = QtGui.QColor(0xB6EEA6)
        for index, (ion, mz, intensity) in enumerate(zip(calibrator.ions, ions_position, ions_intensity)):
            if index in min_indexes:
                def setItem(column, text):
                    item = QtWidgets.QTableWidgetItem(text)
                    item.setBackground(color)
                    table.setItem(index, column, item)
            else:
                def setItem(column, text):
                    item = QtWidgets.QTableWidgetItem(text)
                    table.setItem(index, column, item)

            setItem(0, format(mz, '.5f'))
            setItem(1, format((1 - ion.formula.mass() / mz) * 1e6, '.5f'))
            setItem(2, format(intensity, '.3e'))

        plot = self.plot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        ax.plot(spectrum.mz, spectrum.intensity, color='black')

        for index, (ion, x, y) in enumerate(zip(calibrator.ions, ions_position, ions_intensity)):
            if math.isnan(x):
                continue
            ax.plot([x, x], [0, y], color='r')
            if index in min_indexes:
                ax.annotate(ion.shown_text, (x, y), color='g')
            else:
                ax.annotate(ion.shown_text, (x, y))
        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.legend()
        ax.relim()
        ax.autoscale_view(True, True, True)
        plot.canvas.draw()
        self.spectrum_current_ion_index = -1
        self.shown_state = ShownState.spectrum

    @state_node(withArgs=True)
    def next_ion(self, step):
        if self.spectrum_current_ion_index is None:
            return

        index = self.manager.getters.spectra_list_selected_index.get()
        infos = self.manager.workspace.file_tab.info.spectrum_infos
        calibrator = self.calibration.info.calibrators[infos[index].path]

        index = self.spectrum_current_ion_index = (
            self.spectrum_current_ion_index + step) % len(calibrator.ions)
        inner_index = self.spectrum_inner_index
        ion_position = calibrator.ions_raw_position[inner_index, index]
        ion_intensity = calibrator.ions_raw_intensity[inner_index, index]

        x_min = ion_position - .1
        x_max = ion_position + .1
        y_min = -ion_intensity * .1
        y_max = ion_intensity * 1.2

        plot = self.plot
        ax = plot.ax
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        plot.canvas.draw()

    @state_node
    def showSelected(self):
        if self.shown_state != ShownState.all_info:
            showInfo(
                "please show all info first\nthen choose a file from calibration info window")
            return
        index = self.manager.getters.calibration_info_selected_index.get()

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
        min_indexes = calibrator.min_indexes
        color = QtGui.QColor(0xB6EEA6)
        for i in range(len(calibrator.ions_position)):
            if i in min_indexes:
                def setValue(column, s):
                    item = QtWidgets.QTableWidgetItem(str(s))
                    item.setBackground(color)
                    table.setItem(i, column, item)
            else:
                def setValue(column, s):
                    table.setItem(
                        i, column, QtWidgets.QTableWidgetItem(str(s)))
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
        ax.scatter(x, y, c='green')
        x = ions_position[max_index]
        y = ions_rtol[max_index] * 1e6
        ax.scatter(x, y, c='red')

        ax.set_ylabel('ppm')
        ax.set_xlim(formula_info.mz_min, formula_info.mz_max)
        plot.canvas.draw()

        self.spectrum_current_ion_index = None
        self.shown_state = ShownState.file

    @state_node
    def showAllInfoClicked(self):
        self.showAllInfo()
        self.spectrum_current_ion_index = None

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
        color = QtGui.QColor(0xB6EEA6)
        for row, calibrator in enumerate(calibrators):
            times.append(calibrator.time)

            min_indexes = calibrator.min_indexes
            for column, rtol in enumerate(calibrator.ions_rtol):
                item = QtWidgets.QTableWidgetItem(format(rtol * 1e6, ".5f"))
                if column in min_indexes:
                    item.setBackground(color)
                table.setItem(row, column, item)
            devitions.append(calibrator.ions_rtol)
        vlabels = [time.replace(microsecond=0).isoformat(
            sep=' ')[:-3] for time in times]

        table.setVerticalHeaderLabels(vlabels)

        devitions = np.array(devitions) * 1e6

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
        self.shown_state = ShownState.all_info

    @state_node(withArgs=True)
    def calibrate(self, skip: bool):
        workspace = self.manager.workspace
        rtol = workspace.file_tab.info.rtol
        noise_info = workspace.noise_tab.info
        noise_skip = noise_info.skip
        setting = noise_info.general_setting
        result = noise_info.general_result
        dependent = setting.mass_dependent
        params, points, deltas = setting.get_params(not dependent)
        func_kwargs = {
            "noise_skip": noise_skip,
            "calibrate_skip": skip,
            "rtol": rtol,
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
        msg = []
        if not skip:
            msg.append("calibrate")
        msg.append("merge")
        if not noise_skip:
            msg.append("denoise")
        msg = ', '.join(msg)
        yield calibrate_merge, msg
        self.callback.emit()


class SplitAndFitPeak(MultiProcess):
    @staticmethod
    def read(h5_spectra: StructureListView[Spectrum], **kwargs) -> Generator:
        return h5_spectra

    @staticmethod
    def read_len(h5_spectra: StructureListView[Spectrum], **kwargs) -> int:
        return len(h5_spectra)

    @staticmethod
    def func(data: Spectrum, fit_func: NormalDistributionFunc, ions: List[float], intensity_filter: float, rtol: float, **kwargs):
        ions_peak: List[Tuple[float, float]] = []
        mz = data.mz
        intensity = data.intensity
        for ion in ions:
            delta = ion * rtol
            mz_, intensity_ = spectrum_func.safeCutSpectrum(
                mz, intensity, ion - delta, ion + delta)

            peaks = spectrum_func.splitPeaks(mz_, intensity_)

            # intensity filter for noise
            peaks = [peak for peak in peaks if peak.maxIntensity > 100]

            # find highest peak within rtol
            find = False
            if len(peaks) > 0:
                indexes = np.argsort(peak.maxIntensity for peak in peaks)
                peaks = [peaks[index] for index in indexes]

                while len(peaks) > 0:
                    peak = peaks.pop()
                    target_peaks = fit_func.splitPeak(peak)

                    index = np.argmax(
                        [peak.peak_intensity for peak in target_peaks])
                    peak = target_peaks[index]
                    if abs(peak.peak_position / ion - 1) < rtol:
                        ions_peak.append(
                            (peak.peak_position, peak.peak_intensity))
                        find = True
                        break
            if not find:
                ions_peak.append((math.nan, math.nan))

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
                batch.append((spectrum, funcs.get(spectrum.path, None)))
            else:
                if batch:
                    yield batch
                batch = [(spectrum, funcs.get(spectrum.path, None))]
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
             noise_skip: bool, calibrate_skip: bool, rtol: float,
             quantile: float, mass_dependent: bool, n_sigma: bool,
             dependent: bool, points: np.ndarray, deltas: np.ndarray,
             params: np.ndarray, subtract: bool, poly_coef: np.ndarray) -> Spectrum:
        spectra = []
        paths = set()
        start_times = []
        end_times = []
        for spectrum, func in data:
            if not calibrate_skip:
                spectrum.mz = func.predictMz(spectrum.mz)
            spectra.append((spectrum.mz, spectrum.intensity,
                            (spectrum.end_time - spectrum.start_time).total_seconds()))
            paths.add(spectrum.path)
            start_times.append(spectrum.start_time)
            end_times.append(spectrum.end_time)

        path = paths.pop() if len(paths) == 1 else ""
        mz, intensity = spectrum_func.averageSpectra(
            spectra, rtol, drop_input=True)

        if not noise_skip:
            if not dependent:
                poly_coef, _, slt, params = spectrum_func.getNoiseParams(
                    mz, intensity, quantile, mass_dependent, points, deltas)
                points = points[slt]
                deltas = deltas[slt]

            mz, intensity = spectrum_func.denoiseWithParams(
                mz, intensity, poly_coef, params, points, deltas, n_sigma, subtract)

        start_time = min(start_times)
        end_time = max(end_times)
        spectrum = Spectrum(path, mz, intensity, start_time, end_time)
        return spectrum

    @staticmethod
    def write(file: WorkSpace, rets: Iterable[Spectrum], **kwargs):
        tmp = StructureListView[Spectrum](file._obj, "tmp", True)
        infos = file.calibration_tab.info.calibrated_spectrum_infos
        infos.clear()
        for ret in rets:
            tmp.h5_append(ret)
            infos.append(SpectrumInfo(ret.start_time, ret.end_time))

        target = file.calibration_tab.calibrated_spectra
        path = target.h5_path
        if path in file:
            del file._obj[path]
        file._obj.move(tmp.h5_path, path)

    @staticmethod
    def exception(file, **kwargs):
        if "tmp" in file:
            del file["tmp"]
