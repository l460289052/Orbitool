from enum import Enum
from itertools import chain
from typing import Callable, List, Optional, Tuple, cast

import matplotlib.text
import matplotlib.ticker
import numpy as np
from PyQt5 import QtCore, QtWidgets

from ..functions import binary_search
from ..functions import formula as formula_func
from ..functions import peakfit as peakfit_func
from ..functions import spectrum as spectrum_func
from ..functions.peakfit import masslist as masslist_func
from ..structures.spectrum import (FittedPeak, MassListItem, Peak, PeakTags,
                                   Spectrum)
from ..utils.formula import Formula
from . import PeakFitUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node


class FitMethod(str, Enum):
    restricted_calc = "restricted calc"
    force_calc = "force calc"
    mass_list = "mass list"


class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    show_spectrum = QtCore.pyqtSignal(Spectrum)
    show_masslist = QtCore.pyqtSignal()
    filter_selected = QtCore.pyqtSignal(bool)  # selected or unselected

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)
        manager.signals.peak_refit_finish.connect(self.peak_refit_finish)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start()
        self.plot_lim: Tuple[Tuple[int, int], Tuple[int, int]] = None

    def setupUi(self, Form):
        super().setupUi(Form)

        self.filterTagComboBox.addItems([tag.name for tag in PeakTags])
        self.addTagComboBox.addItems([tag.name for tag in PeakTags])
        self.fitComboBox.addItem("standard calc", FitMethod.restricted_calc)
        self.fitComboBox.addItem("unrestricted calc", FitMethod.force_calc)
        self.fitComboBox.addItem("mass list", FitMethod.mass_list)

        self.showSelectedPushButton.clicked.connect(self.showSelect)
        self.filterSelectYToolButton.clicked.connect(self.filterSelected)
        self.filterSelectNToolButton.clicked.connect(self.filterUnselected)
        self.filterFormulaYToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_formula_y))
        self.filterFormulaNToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_formula_n))
        self.filterStableIsotopeYToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_stable_y))
        self.filterStableIsotopeNToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_stable_n))
        self.filterTagYToolButton.clicked.connect(
            lambda: self.filter_tag(True))
        self.filterTagNToolButton.clicked.connect(
            lambda: self.filter_tag(False))
        self.filterIntensityMaxToolButton.clicked.connect(
            self.filter_intensity_max)
        self.filterIntensityMinToolButton.clicked.connect(
            self.filter_intensity_min)
        self.filterMassDefectToolButton.clicked.connect(
            self.filter_mass_defect)
        self.filterGroupToolButton.clicked.connect(
            self.filter_group)

        self.filterClearPushButton.clicked.connect(self.filterClear)

        self.fitPushButton.clicked.connect(self.fit)
        self.addTagPushButton.clicked.connect(self.add_tag)
        self.actionAddToMassListPushButton.clicked.connect(self.addToMassList)
        self.actionRmTagPushButton.clicked.connect(self.remove_tag)

        self.plot = Plot(self.widget)
        self.manager.bind.peak_fit_left_index.connect(
            "peakfit", self.move_plot_to_index)

        self.scaleToSpectrumPushButton.clicked.connect(self.scale_spectrum)
        self.yLogcheckBox.toggled.connect(self.ylog_toggle)
        self.rescaleToolButton.clicked.connect(self.rescale_clicked)
        self.leftToolButton.clicked.connect(lambda: self.moveRight(-1))
        self.rightToolButton.clicked.connect(lambda: self.moveRight(1))
        self.yLimDoubleToolButton.clicked.connect(lambda: self.y_times(2))
        self.yLimHalfToolButton.clicked.connect(lambda: self.y_times(.5))

    def restore(self):
        self.show_and_plot()
        self.peakfit.ui_state.set_state(self)

    def updateState(self):
        self.peakfit.ui_state.fromComponents(self, [
            self.yLogcheckBox])

    def show_and_plot(self):
        self.manager.signals.peak_list_show.emit()
        if self.peakfit.info.spectrum:
            self.plot_peaks()

    @property
    def peakfit(self):
        return self.manager.workspace.peakfit_tab

    @state_node
    def showSelect(self):
        workspace = self.manager.workspace
        selected_index = self.manager.getters.spectra_list_selected_index.get()

        def read():
            spectrum = workspace.calibration_tab.calibrated_spectra[
                selected_index]
            raw_peaks = spectrum_func.splitPeaks(
                spectrum.mz, spectrum.intensity)
            return spectrum, raw_peaks

        spectrum, raw_peaks = yield read, "read spectrum"

        raw_split_num, original_indexes, peaks = yield SplitPeaks(raw_peaks, func_kwargs={
            "func": workspace.peak_shape_tab.info.func}), "fit use peak shape func"

        peaks = cast(List[FittedPeak], peaks)
        manager = self.manager

        def formula_and_residual():
            calc = workspace.formula_docker.info.restricted_calc
            calc_get = workspace.formula_docker.info.restricted_calc_get
            for peak in manager.tqdm(peaks, msg="init formula"):
                calc_get(peak.peak_position)

            for peak in manager.tqdm(peaks):
                peak.formulas = calc_get(peak.peak_position)
                peak.formulas = formula_func.correct(peak, peaks, calc.rtol)

            mz, residual = peakfit_func.calculateResidual(
                raw_peaks, original_indexes, peaks, workspace.peak_shape_tab.info.func)

            return mz, residual

        mz, residual = yield formula_and_residual, "calc formula"

        info = self.peakfit.info
        info.spectrum, info.raw_peaks = spectrum, raw_peaks
        info.raw_split_num = raw_split_num
        info.original_indexes = original_indexes
        info.peaks = peaks
        info.residual_mz, info.residual_intensity = mz, residual
        info.shown_indexes = list(range(len(info.peaks)))

        self.show_spectrum.emit(info.spectrum)
        self.show_and_plot()

    def peak_refit_finish(self):
        self.manager.signals.peak_list_show.emit()

    def plot_peaks(self):
        info = self.peakfit.info
        plot = self.plot
        is_log = self.yLogcheckBox.isChecked()
        ax = plot.ax
        ax.clear()

        ax.axhline(color='k', linewidth=.5)
        ax.yaxis.set_tick_params(rotation=45)

        ax.set_yscale('log' if is_log else 'linear')
        if is_log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.plot(info.spectrum.mz, info.spectrum.intensity,
                color='k', linewidth=1, label="spectrum")
        ax.plot(info.residual_mz, info.residual_intensity,
                color='r', linewidth=.5, label="residual")
        ax.legend()

        mi = info.spectrum.mz.min()
        ma = info.spectrum.mz.max()
        ll, lr = ax.get_xlim()
        ax.set_xlim(mi if ll > mi else ll, ma if lr < ma else lr)

        self.rescale()

        plot.canvas.draw()

    @state_node(withArgs=True)
    def ylog_toggle(self, is_log):
        ax = self.plot.ax
        ax.set_yscale('log' if is_log else 'linear')
        if not is_log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        self.rescale()
        self.plot.canvas.draw()

    @state_node(mode='n', withArgs=True)
    def moveRight(self, step):
        plot = self.plot
        x_min, x_max = plot.ax.get_xlim()
        plot.ax.set_xlim(x_min + step, x_max + step)
        self.plot.canvas.draw()

    @state_node(mode='n', withArgs=True)
    def y_times(self, times):
        plot = self.plot
        y_min, y_max = plot.ax.get_ylim()
        y_max *= times
        if not self.yLogcheckBox.isChecked():
            y_min = - 0.025 * y_max
        plot.ax.set_ylim(y_min, y_max)
        plot.canvas.draw()

    @state_node
    def rescale_clicked(self):
        self.rescale()
        self.plot.canvas.draw()

    def rescale(self):
        spectrum = self.peakfit.info.spectrum
        if spectrum is None:
            return

        plot = self.plot
        x_min, x_max = plot.ax.get_xlim()
        id_min, id_max = binary_search.indexBetween_np(
            spectrum.mz, (x_min, x_max))
        if id_min >= id_max:
            return
        y_max = spectrum.intensity[id_min:id_max].max()

        if self.yLogcheckBox.isChecked():
            y_min = .1
            y_max *= 2
        else:
            dy = 0.05 * y_max
            y_min = -dy
            y_max += dy

        plot.ax.set_xlim(x_min, x_max)
        plot.ax.set_ylim(y_min, y_max)

    @state_node
    def scale_spectrum(self):
        info = self.peakfit.info
        if info.spectrum is None:
            return
        spectrum = info.spectrum
        self.plot.ax.set_xlim(spectrum.mz.min(), spectrum.mz.max())

        self.rescale()

        self.plot.canvas.draw()

    def move_plot_to_index(self, index):
        peaks = self.peakfit.info.peaks
        indexes = self.peakfit.info.shown_indexes
        ax = self.plot.ax

        if not indexes:
            return
        peak = peaks[indexes[index]]
        new_x_min = peak.mz.min()
        x_min, x_max = ax.get_xlim()
        new_x_max = new_x_min + (x_max - x_min)
        ax.set_xlim(new_x_min, new_x_max)

        self.plot_moved()

    @state_node(mode='n')
    def timer_timeout(self):
        ax = self.plot.ax
        now_lim = (ax.get_xlim(), ax.get_ylim())
        if self.plot_lim is not None and abs(np.array(now_lim) / np.array(self.plot_lim) - 1).max() < 1e-3:
            return

        (x_min, x_max), (y_min, y_max) = now_lim
        peaks = self.peakfit.info.peaks
        indexes = self.peakfit.info.shown_indexes

        index = binary_search.indexFirstBiggerThan(
            indexes, x_min, method=lambda indexes, ind: peaks[indexes[ind]].peak_position)

        self.manager.bind.peak_fit_left_index.emit_except("peakfit", index)
        self.plot_moved()

    def plot_moved(self):
        ax = self.plot.ax

        now_lim = (ax.get_xlim(), ax.get_ylim())
        self.plot_lim = now_lim

        raw_peaks = self.peakfit.info.raw_peaks
        original_indexes = self.peakfit.info.original_indexes
        peaks = self.peakfit.info.peaks
        indexes = self.peakfit.info.shown_indexes

        (x_min, x_max), (y_min, y_max) = now_lim

        s = binary_search.indexBetween(
            indexes, (x_min, x_max), method=lambda indexes, ind: peaks[indexes[ind]].peak_position)
        indexes = indexes[s]
        index_peaks_pair = [(index, peak) for index in indexes if y_min < (
            peak := peaks[index]).peak_intensity < y_max]
        args = np.array([peak.peak_intensity for _, peak in index_peaks_pair],
                        dtype=float).argsort()[::-1]

        anns = [child for child in ax.get_children() if isinstance(
            child, matplotlib.text.Annotation)]
        while anns:
            ann = anns.pop()
            ann.remove()
            del ann

        cnt = 0
        for arg in args:
            index, peak = index_peaks_pair[arg]
            if len(peak.formulas) == 0:
                continue
            raw_peak = raw_peaks[original_indexes[index]]
            ind = binary_search.indexNearest_np(
                raw_peak.mz, peak.peak_position)
            ax.annotate(
                ','.join([str(f) for f in peak.formulas]),
                xy=(raw_peak.mz[ind], raw_peak.intensity[ind]),
                xytext=(peak.peak_position, peak.peak_intensity),
                arrowprops={"arrowstyle": "-", "alpha": .5})

            cnt += 1
            if cnt == 5:
                break
        self.plot.canvas.draw()

    @state_node
    def filterClear(self):
        info = self.peakfit.info
        info.shown_indexes = list(range(len(info.peaks)))
        self.manager.signals.peak_list_show.emit()

    @state_node
    def filterSelected(self):
        self.filter_selected.emit(True)
        self.manager.signals.peak_list_show.emit()

    @state_node
    def filterUnselected(self):
        self.filter_selected.emit(False)
        self.manager.signals.peak_list_show.emit()

    @state_node(withArgs=True)
    def filterGeneral(self, filter: Callable[[FittedPeak], bool]):
        self._filter_general(filter)

    def _filter_general(self, filter: Callable[[FittedPeak], bool]):
        info = self.peakfit.info
        peaks = info.peaks
        info.shown_indexes = [
            index for index in info.shown_indexes if filter(peaks[index])]
        self.manager.signals.peak_list_show.emit()

    @state_node(withArgs=True)
    def filter_tag(self, y: bool):
        tag = self.filterTagComboBox.currentText()
        tag: PeakTags = getattr(PeakTags, tag)
        if y:
            self._filter_general(lambda fp: tag.value in fp.tags)
        else:
            self._filter_general(lambda fp: tag.value not in fp.tags)

    @state_node
    def filter_intensity_max(self):
        value = self.filterIntensityMaxDoubleSpinBox.value()
        self._filter_general(lambda fp: fp.peak_intensity < value)

    @state_node
    def filter_intensity_min(self):
        value = self.filterIntensityMinDoubleSpinBox.value()
        self._filter_general(lambda fp: fp.peak_intensity > value)

    @state_node
    def filter_mass_defect(self):
        mi = self.filterMassDefectMinDoubleSpinBox.value()
        ma = self.filterMassDefectMaxDoubleSpinBox.value()
        self._filter_general(
            lambda fp: mi < fp.peak_position - round(fp.peak_position) < ma)

    @state_node
    def filter_group(self):
        group = self.filterGroupLineEdit.text()
        group = Formula(group)
        self._filter_general(lambda fp: any(group in f for f in fp.formulas))

    @state_node(withArgs=True)
    def generalAction(self, action: Callable[[FittedPeak], None], msg: str):
        yield from self._general_action(action, msg)

    def _general_action(self, action: Callable[[FittedPeak], None], msg: str):
        info = self.peakfit.info

        peaks = info.peaks
        indexes = info.shown_indexes

        manager = self.manager

        def func():
            for index in manager.tqdm(indexes):
                action(peaks[index])

        yield func, msg

        self.manager.signals.peak_list_show.emit()

    @state_node
    def fit(self):
        method: FitMethod = self.fitComboBox.currentData()
        if method == FitMethod.restricted_calc:
            yield from self.fit_formula()
        elif method == FitMethod.force_calc:
            yield from self.fit_force_formula()
        elif method == FitMethod.mass_list:
            yield from self.fit_mass_list()

    def fit_formula(self):
        info = self.peakfit.info

        calc = self.manager.workspace.formula_docker.info.restricted_calc
        calc_get = self.manager.workspace.formula_docker.info.restricted_calc_get
        peaks = info.peaks
        indexes = info.shown_indexes

        manager = self.manager

        def func():
            for peak in manager.tqdm(peaks, msg="init formula"):
                calc_get(peak.peak_position)  # init
            for index in manager.tqdm(indexes):
                peak = peaks[index]
                peak.formulas = calc_get(peak.peak_position)
                peak.formulas = formula_func.correct(peak, peaks, calc.rtol)

        yield func, "fit use restricted calc"

        self.manager.signals.peak_list_show.emit()

    def fit_force_formula(self):
        calc_get = self.manager.workspace.formula_docker.info.force_calc_get

        def proc(fp: FittedPeak):
            fp.formulas = calc_get(fp.peak_position)
        yield from self._general_action(proc, "fit use unrestricted calc")

    def fit_mass_list(self):
        rtol = self.manager.workspace.masslist_docker.info.rtol
        masslist = self.manager.workspace.masslist_docker.info.masslist

        def proc(fp: FittedPeak):
            fp.formulas = masslist_func.fitUseMassList(
                fp.peak_position, masslist, rtol)

        yield from self._general_action(proc, "fit use mass list")

    @state_node
    def add_tag(self):
        tag = self.addTagComboBox.currentText()
        tag: PeakTags = getattr(PeakTags, tag)

        def proc(fp: FittedPeak):
            fp.tags = tag.value
        yield from self._general_action(proc, "add tag")

    @state_node
    def addToMassList(self):
        masslist = self.manager.workspace.masslist_docker.info.masslist
        rtol = self.manager.workspace.masslist_docker.info.rtol

        yield from self._general_action(lambda fp: masslist_func.addMassTo(
            masslist, MassListItem(position=fp.peak_position, formulas=fp.formulas), rtol=rtol), "add to mass list")

        self.show_masslist.emit()

    @state_node
    def remove_tag(self):
        def proc(fp: FittedPeak):
            fp.tags = ""
        yield from self._general_action(proc, "add tag")


class SplitPeaks(MultiProcess):
    @staticmethod
    def read(raw_peaks: List[Peak], **kwargs):
        for peak in raw_peaks:
            yield peak

    @staticmethod
    def read_len(raw_peaks: List[Peak], **kwargs) -> int:
        return len(raw_peaks)

    @staticmethod
    def func(peak: Peak, func: peakfit_func.BaseFunc):
        return func.splitPeak(peak)

    @staticmethod
    def write(file, rets):
        peaks = []
        original_indexes = []
        split_num = []
        for index, ret in enumerate(rets):
            split_num.append(len(ret))
            for peak in ret:
                peaks.append(peak)
                original_indexes.append(index)
        return split_num, original_indexes, peaks

    @staticmethod
    def exception(file, **kwargs):
        pass


def filter_formula_y(fp: FittedPeak):
    return len(fp.formulas) > 0


def filter_formula_n(fp: FittedPeak):
    return len(fp.formulas) == 0


def filter_stable_y(fp: FittedPeak):
    return any(not f.isIsotope for f in fp.formulas)


def filter_stable_n(fp: FittedPeak):
    return any(f.isIsotope for f in fp.formulas)
