from functools import partial
import math
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union
from itertools import chain

import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

from ..functions import spectrum as spectrum_func, binary_search, peakfit as peakfit_func
from ..functions.calibration import Calibrator
from ..functions.peakfit.normal_distribution import NormalDistributionFunc
from ..structures.HDF5 import StructureListView, DiskListDirectView
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..workspace import WorkSpace
from ..workspace.calibration import CalibratorInfoSegment
from . import CalibrationUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row, showInfo, DragHelper, openfile, savefile
from Orbitool import setting

from .CalibrationDetailUiPy import Widget as CalibrationDetailWin


class ShownState(int, Enum):
    all_info = 0
    spectrum = 1
    file = 2


class Widget(QtWidgets.QWidget):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.ui = CalibrationUi.Ui_Form()
        self.drag_helper = DragHelper(("file","text"))
        self.setupUi()
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.ionsTableWidget.dragEnterEvent = self.tableDragEnterEvent
        ui.ionsTableWidget.dragMoveEvent = self.tableDragMoveEvent
        ui.ionsTableWidget.dropEvent = self.tableDropEvent
        ui.addIonToolButton.clicked.connect(self.addIon)
        ui.delIonToolButton.clicked.connect(self.removeIon)
        ui.ionsImportToolButton.clicked.connect(self.importIons)
        ui.ionsExportToolButton.clicked.connect(self.exportIons)

        self.plot = Plot(ui.figureTabWidgetPage)
        ui.tabWidget.setCurrentIndex(0)

        ui.separatorListWidget.itemDoubleClicked.connect(self.changeSegment)
        ui.separatorListWidget.mouseReleaseEvent = self.mouseRelease
        ui.separatorAddPushButton.clicked.connect(self.addSegment)

        ui.calcInfoPushButton.clicked.connect(self.calcInfo)
        ui.showDetailsPushButton.clicked.connect(self.showDetail)
        ui.finishPushButton.clicked.connect(
            lambda: self.calibrate(skip=False))
        ui.skipPushButton.clicked.connect(lambda: self.calibrate(skip=True))

    @property
    def info(self):
        return self.manager.workspace.info.calibration_tab

    def restore(self):
        self.showSegments()
        self.showCurrentSegment()
        self.info.ui_state.restore_state(self.ui)
        self.showAllInfo()

    def updateState(self):
        self.info.ui_state.store_state(self)

    def showSegments(self):
        workspace = self.manager.workspace
        begin_point = workspace.info.formula_docker.mz_min
        end_point = workspace.info.formula_docker.mz_max

        listwidget = self.ui.separatorListWidget
        listwidget.clear()
        points = [
            seg.end_point for seg in self.info.calibrate_info_segments]
        points.pop()
        for begin, end in zip([begin_point, *points], [*points, end_point]):
            listwidget.addItem("{:.2f}-{:.2f}".format(begin, end))

    def showCurrentSegment(self):
        info = self.info
        ui = self.ui
        ind = info.current_segment_index
        ui.separatorListWidget.setCurrentRow(ind)
        seg = info.calibrate_info_segments[ind]
        table = ui.ionsTableWidget
        table.clearContents()
        ions = info.get_ions_for_segment(ind)
        table.setRowCount(len(ions))
        for index, ion in enumerate(ions):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ion.shown_text))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(format(ion.formula.mass(), ".4f")))

        ui.filterSpinBox.setValue(seg.intensity_filter)
        ui.degreeSpinBox.setValue(seg.degree)
        ui.nIonsSpinBox.setValue(seg.n_ions)

    def saveCurrentSegment(self):
        info = self.info
        ui = self.ui
        seg = info.calibrate_info_segments[info.current_segment_index]
        seg.intensity_filter = ui.filterSpinBox.value()
        seg.degree = ui.degreeSpinBox.value()
        seg.n_ions = ui.nIonsSpinBox.value()

    @state_node
    def addSegment(self):
        ui = self.ui
        separator = ui.separatorDoubleSpinBox.value()
        formula_info = self.manager.workspace.info.formula_docker
        assert formula_info.mz_min < separator < formula_info.mz_max, "please check mz range in formula docker"
        self.info.add_segment(separator)
        self.showSegments()
        self.showCurrentSegment()

    @state_node(mode='n', withArgs=True)
    def mouseRelease(self, e: QtGui.QMouseEvent):
        ui = self.ui
        indexes = [ind.row()
                   for ind in ui.separatorListWidget.selectedIndexes()]
        if len(indexes) > 1:
            menu = QtWidgets.QMenu(self)

            merge = QtWidgets.QAction('merge', menu)

            func = partial(self.mergeSegment, indexes)
            merge.triggered.connect(lambda: func())
            menu.addAction(merge)
            menu.popup(e.globalPos())
        return QtWidgets.QListWidget.mouseReleaseEvent(ui.separatorListWidget, e)

    @state_node(withArgs=True)
    def mergeSegment(self, indexes: List[int]):
        ma = max(indexes)
        mi = min(indexes)
        assert ma - mi == len(indexes) - \
            1, "cannot merge unjoined segments"
        info = self.info
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

        ind = self.ui.separatorListWidget.row(item)
        self.info.current_segment_index = ind

        self.showCurrentSegment()

    @state_node
    def addIon(self):
        self.info.add_ions(self.ui.ionsLineEdit.text().split(','))
        self.showCurrentSegment()

    @state_node
    def removeIon(self):
        remove_ions = set()
        for index in get_tablewidget_selected_row(self.ui.ionsTableWidget):
            remove_ions.add(self.ui.ionsTableWidget.item(index, 0).text())
        self.info.ions = [
            ion for ion in self.info.ions if ion.shown_text not in remove_ions]
        self.showCurrentSegment()

    @state_node
    def importIons(self):
        ret, f = openfile("Open calibration ions file", "*.csv")
        if not ret:
            return
        f = Path(f)
        backup = self.info.ions
        self.info.ions = []
        try:
            self.info.add_ions(f.read_text().split()[1:])
        except:
            self.info.ions = backup
            raise
    
    @state_node
    def exportIons(self):
        ret, f = savefile("Save calibration ions", "*.csv")
        if not ret:
            return
        f = Path(f)
        l = ["Ion"]
        l.extend(ion.shown_text for ion in self.info.ions)
        f.write_text("\n".join(l))


    @state_node(mode="e", withArgs=True)
    def tableDragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if self.drag_helper.accept(event.mimeData()):
            event.setDropAction(QtCore.Qt.DropAction.LinkAction)
            event.accept()
    
    @state_node(mode="e", withArgs=True)
    def tableDragMoveEvent(self, event: QtGui.QDragMoveEvent):
        event.accept()
    
    @state_node(withArgs=True)
    def tableDropEvent(self, event:QtGui.QDropEvent):
        ions = []
        for f in self.drag_helper.yield_file(event.mimeData()):
            if f.suffix.lower() in {".txt", ".csv"}:
                ions.extend(f.read_text().splitlines()[1:])
        text = self.drag_helper.get_text(event.mimeData())
        ions.extend(text.replace(",", "\t").split())
        if setting.calibration.dragdrop_ion_replace:
            backup = self.info.ions
            self.info.ions = []
            try:
                self.info.add_ions(ions)
            except:
                self.info.ions = backup
                raise
        else:
            self.info.add_ions(ions)
        self.showCurrentSegment()


    @state_node
    def calcInfo(self):
        workspace = self.manager.workspace
        info = self.info

        intensity_filter = 100
        self.saveCurrentSegment()

        rtol = self.ui.rtolDoubleSpinBox.value() * 1e-6
        if workspace.info.noise_tab.to_be_calibrate or abs(info.rtol / rtol - 1) > 1e-6:
            formulas = [ion.formula for ion in info.ions]
            all_ions = True
        else:
            formulas = info.need_split()
            all_ions = False

        raw_spectra = workspace.data.raw_spectra

        if formulas:
            func = SplitAndFitPeak(
                raw_spectra,
                func_kwargs=dict(
                    fit_func=workspace.info.peak_shape_tab.func,
                    ions=[formula.mass() for formula in formulas],
                    segments=info.calibrate_info_segments,
                    rtol=rtol))

            path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = yield func, "split and fit target peaks"

            def func():
                info.path_times = {
                    path.path: path.createDatetime for path in workspace.info.file_tab.pathlist}
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

    def showAllInfo(self):
        info = self.info

        table = self.ui.caliInfoTableWidget
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
        deviations = []
        color = QtGui.QColor(0xB6EEA6)
        for row, (path, time) in enumerate(path_times):
            ion_infos = path_ion_infos[path]
            deviation = []
            for col, (ion, used) in enumerate(info.yield_ion_used(path)):
                rtol = ion_infos[ion.formula].rtol
                item = QtWidgets.QTableWidgetItem(format(rtol * 1e6, ".5f"))
                if used:
                    item.setBackground(color)
                table.setItem(row, col, item)
                deviation.append(rtol)
            deviations.append(deviation)

        vlabels = [str(time.replace(microsecond=0))[:-3] for time in times]

        table.setVerticalHeaderLabels(vlabels)

        deviations = np.array(deviations) * 1e6

        plot = self.plot

        ax = plot.ax
        ax.clear()
        ax.axhline(color="k", linewidth=.5)

        if len(deviations) > 0:
            kwds = {}
            if len(times) == 1:
                kwds["marker"] = "."
            for index in range(deviations.shape[1]):
                ax.plot(times, deviations[:, index], **kwds,
                        label=info.last_ions[index].shown_text)

        ax.set_xlabel("starting time")
        ax.set_ylabel("Deviation (ppm)")
        ax.xaxis.set_tick_params(rotation=15)
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
        rtol = workspace.info.file_tab.rtol
        noise_info = workspace.info.noise_tab
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
            "poly_coef": result.poly_coef,
            "std": result.global_noise_std}
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
        data = file.data
        noise_tab = file.info.noise_tab
        separators = np.array([
            info.end_point for info in file.info.calibration_tab.last_calibrate_info_segments])

        batch = []
        calibrators_segments = file.info.calibration_tab.calibrator_segments
        for info, spectrum in zip(noise_tab.denoised_spectrum_infos, data.raw_spectra):
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
        for info in file.info.noise_tab.denoised_spectrum_infos:
            if info.average_index == 0:
                cnt += 1
        return cnt

    @staticmethod
    def func(data: List[Tuple[Spectrum, List[float], List[Calibrator]]],
             noise_skip: bool, calibrate_skip: bool, average_rtol: float,
             quantile: float, mass_dependent: bool, n_sigma: bool,
             dependent: bool, points: np.ndarray, deltas: np.ndarray,
             params: np.ndarray, subtract: bool, poly_coef: np.ndarray, std: float) -> Spectrum:
        spectra = []
        paths = set()
        start_times = []
        end_times = []
        calibrator: Calibrator
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
                poly_coef, std, slt, params = spectrum_func.getNoiseParams(
                    mz, intensity, quantile, mass_dependent, points, deltas)
                points = points[slt]
                deltas = deltas[slt]

            mz, intensity = spectrum_func.denoiseWithParams(
                mz, intensity, poly_coef, std, params, points, deltas, n_sigma, subtract)

        start_time = min(start_times)
        end_time = max(end_times)
        spectrum = Spectrum(path, mz, intensity, start_time, end_time)
        return spectrum

    @staticmethod
    def write(file: WorkSpace, rets: Iterable[Spectrum], **kwargs):
        obj = (file.proxy_file or file.file)._obj
        tmp = DiskListDirectView(obj, "tmp")
        infos = []

        def it():
            for spectrum in rets:
                infos.append(SpectrumInfo(spectrum.start_time, spectrum.end_time))
                yield spectrum
        tmp.extend(it())
        file.info.calibration_tab.calibrated_spectrum_infos = infos
        path = file.data.calibrated_spectra.obj.name
        del obj[path]
        obj.move(tmp.obj.name, path)

    @staticmethod
    def exception(file: WorkSpace, **kwargs):
        obj = (file.proxy_file or file.file)._obj
        if "tmp" in obj:
            del obj["tmp"]
