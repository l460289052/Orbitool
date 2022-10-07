from functools import partial
import math
from enum import Enum
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union
from itertools import chain

import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.ticker

from ..functions import spectrum as spectrum_func, binary_search, peakfit as peakfit_func
from ..functions.calibration import Calibrator
from ..functions.peakfit.normal_distribution import NormalDistributionFunc
from ..structures.HDF5 import StructureListView
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..workspace import WorkSpace
from ..workspace.calibration import CalibratorInfoSegment
from . import CalibrationUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row, showInfo

from .CalibrationDetailUiPy import Widget as CalibrationDetailWin


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

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = Plot(self.figureTabWidgetPage)
        self.tabWidget.setCurrentIndex(0)

        self.separatorListWidget.itemDoubleClicked.connect(self.changeSegment)
        self.separatorListWidget.mouseReleaseEvent = self.mouseRelease
        self.separatorAddPushButton.clicked.connect(self.addSegment)

        self.addIonToolButton.clicked.connect(self.addIon)
        self.delIonToolButton.clicked.connect(self.removeIon)
        self.calcInfoPushButton.clicked.connect(self.calcInfo)
        self.showDetailsPushButton.clicked.connect(self.showDetail)
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
        self.showAllInfo()

    def updateState(self):
        self.calibration.ui_state.fromComponents(self, [
            self.rtolDoubleSpinBox,
            self.filterSpinBox,
            self.degreeSpinBox,
            self.nIonsSpinBox])

    def showSegments(self):
        workspace = self.manager.workspace
        begin_point = workspace.formula_docker.info.mz_min
        end_point = workspace.formula_docker.info.mz_max

        listwidget = self.separatorListWidget
        listwidget.clear()
        points = [
            seg.end_point for seg in self.calibration.info.calibrate_info_segments]
        points.pop()
        for begin, end in zip([begin_point, *points], [*points, end_point]):
            listwidget.addItem("{:.2f}-{:.2f}".format(begin, end))

    def showCurrentSegment(self):
        info = self.calibration.info
        ind = info.current_segment_index
        self.separatorListWidget.setCurrentRow(ind)
        seg = info.calibrate_info_segments[ind]
        table = self.ionsTableWidget
        table.clearContents()
        ions = info.get_ions_for_segment(ind)
        table.setRowCount(len(ions))
        for index, ion in enumerate(ions):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ion.shown_text))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(format(ion.formula.mass(), ".4f")))

        self.filterSpinBox.setValue(seg.intensity_filter)
        self.degreeSpinBox.setValue(seg.degree)
        self.nIonsSpinBox.setValue(seg.n_ions)

    def saveCurrentSegment(self):
        info = self.calibration.info
        seg = info.calibrate_info_segments[info.current_segment_index]
        seg.intensity_filter = self.filterSpinBox.value()
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
        self.saveCurrentSegment()

        ind = self.separatorListWidget.row(item)
        self.calibration.info.current_segment_index = ind

        self.showCurrentSegment()

    @state_node
    def addIon(self):
        self.calibration.info.add_ions(self.ionLineEdit.text().split(','))
        self.showCurrentSegment()

    @state_node
    def removeIon(self):
        remove_ions = set()
        for index in get_tablewidget_selected_row(self.ionsTableWidget):
            remove_ions.add(self.ionsTableWidget.item(index, 0).text())
        self.calibration.info.ions = [
            ion for ion in self.calibration.info.ions if ion.shown_text not in remove_ions]
        self.showCurrentSegment()

    @state_node
    def calcInfo(self):
        workspace = self.manager.workspace
        calibration_tab = self.calibration
        info = calibration_tab.info

        intensity_filter = 100
        self.saveCurrentSegment()

        rtol = self.rtolDoubleSpinBox.value() * 1e-6
        if workspace.noise_tab.info.to_be_calibrate or abs(info.rtol / rtol - 1) > 1e-6:
            formulas = [ion.formula for ion in info.ions]
            all_ions = True
        else:
            formulas = info.need_split()
            all_ions = False

        raw_spectra = workspace.noise_tab.raw_spectra

        if formulas:
            func = SplitAndFitPeak(
                raw_spectra,
                func_kwargs=dict(
                    fit_func=workspace.peak_shape_tab.info.func,
                    ions=[formula.mass() for formula in formulas],
                    segments=info.calibrate_info_segments,
                    rtol=rtol))

            path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = yield func, "split and fit target peaks"

            def func():
                info.path_times = {
                    path.path: path.createDatetime for path in workspace.file_tab.info.pathlist}
                if all_ions:
                    info.last_ions.clear()
                    info.path_ion_infos.clear()
                info.done_split(path_ions_peak)
                info.rtol = rtol
            yield func, "calculate ions points"

        def func():
            info.calc_calibrator()

        yield func, "calculate calibration infos"

        self.showAllInfo()

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

    def showAllInfo(self):
        info = self.calibration.info

        table = self.caliInfoTableWidget
        table.clearContents()
        table.setColumnCount(len(info.last_ions))
        hlables = [ion.shown_text for ion in info.last_ions]
        table.setHorizontalHeaderLabels(hlables)

        path_ion_infos = info.path_ion_infos
        table.setRowCount(len(path_ion_infos))
        if len(info.calibrator_segments) == 0:
            return

        path_times = [(path, info.path_times[path])
                      for path in path_ion_infos.keys()]
        path_times.sort(key=lambda t: t[1])

        segment_ions = list(info.yield_segment_ions())
        times = [time for _, time in path_times]
        devitions = []
        color = QtGui.QColor(0xB6EEA6)
        for row, (path, time) in enumerate(path_times):
            ion_infos = path_ion_infos[path]
            devition = []
            for col, (ion, used) in enumerate(info.yield_ion_used(path)):
                rtol = ion_infos[ion.formula].rtol
                item = QtWidgets.QTableWidgetItem(format(rtol * 1e6, ".5f"))
                if used:
                    item.setBackground(color)
                table.setItem(row, col, item)
                devition.append(rtol)
            devitions.append(devition)

        vlabels = [str(time.replace(microsecond=0))[:-3] for time in times]

        table.setVerticalHeaderLabels(vlabels)

        devitions = np.array(devitions) * 1e6

        plot = self.plot

        ax = plot.ax
        ax.clear()
        ax.axhline(color="k", linewidth=.5)

        if len(devitions) > 0:
            for index in range(devitions.shape[1]):
                ax.plot(times, devitions[:, index],
                        label=info.last_ions[index].shown_text)

        ax.set_xlabel("starting time")
        ax.set_ylabel("Deviation (ppm)")
        ax.legend()
        ax.relim()
        ax.autoscale(True, True, True)
        plot.canvas.draw()

    @state_node
    def showDetail(self):
        win = CalibrationDetailWin(self.manager)
        self.manager.calibration_detail_win = win
        win.show()

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
            "average_rtol": rtol,
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
    def func(data: Spectrum, fit_func: NormalDistributionFunc, ions: List[float], rtol: float, segments: List[CalibratorInfoSegment], **kwargs):
        ions_peak: List[Tuple[float, float]] = []
        mz = data.mz
        intensity = data.intensity
        segment_index = 0
        for ion in ions:
            while segments[segment_index].end_point < ion:
                segment_index += 1
            delta = ion * rtol
            mz_, intensity_ = spectrum_func.safeCutSpectrum(
                mz, intensity, ion - delta, ion + delta)

            peaks = spectrum_func.splitPeaks(mz_, intensity_)

            # intensity filter for noise
            peaks = [peak for peak in peaks if peak.maxIntensity >
                     segments[segment_index].intensity_filter]

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
        # path -> [[(position, intensity) for each ion] for each spectrum]
        for path, ions_peak in rets:
            path_ions_peak.setdefault(path, []).append(ions_peak)
        return path_ions_peak

    @staticmethod
    def exception(file, **kwargs):
        pass


class CalibrateMergeDenoise(MultiProcess):
    @staticmethod
    def read(file: WorkSpace, **kwargs) -> Generator[List[Tuple[Spectrum, Calibrator]], Any, Any]:
        noise_tab = file.noise_tab
        separators = np.array([
            info.end_point for info in file.calibration_tab.info.last_calibrate_info_segments])

        batch = []
        calibrators_segments = file.calibration_tab.info.calibrator_segments
        for info, spectrum in zip(noise_tab.info.denoised_spectrum_infos, noise_tab.raw_spectra):
            item = (spectrum, separators,
                    calibrators_segments.get(spectrum.path, None))
            if info.average_index:
                batch.append(item)
            else:
                if batch:
                    yield batch
                batch = [item]
        yield batch

    @staticmethod
    def read_len(file: WorkSpace, **read_kwargs) -> int:
        cnt = 0
        for info in file.noise_tab.info.denoised_spectrum_infos:
            if info.average_index == 0:
                cnt += 1
        return cnt

    @staticmethod
    def func(data: List[Tuple[Spectrum, List[float], List[Calibrator]]],
             noise_skip: bool, calibrate_skip: bool, average_rtol: float,
             quantile: float, mass_dependent: bool, n_sigma: bool,
             dependent: bool, points: np.ndarray, deltas: np.ndarray,
             params: np.ndarray, subtract: bool, poly_coef: np.ndarray) -> Spectrum:
        spectra = []
        paths = set()
        start_times = []
        end_times = []
        for spectrum, separators, calibrators in data:
            if not calibrate_skip:
                mz = []
                for mz_part, calibrator in zip(spectrum_func.safeSplitSpectrum(spectrum.mz, spectrum.intensity, separators), calibrators):
                    mz.append(calibrator.calibrate_mz(mz_part))
                spectrum.mz = np.concatenate(mz)
            spectra.append((spectrum.mz, spectrum.intensity,
                            (spectrum.end_time - spectrum.start_time).total_seconds()))
            paths.add(spectrum.path)
            start_times.append(spectrum.start_time)
            end_times.append(spectrum.end_time)

        path = paths.pop() if len(paths) == 1 else ""
        mz, intensity = spectrum_func.averageSpectra(
            spectra, average_rtol, drop_input=True)

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
