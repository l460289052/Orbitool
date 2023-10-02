from enum import Enum
from itertools import chain
from typing import Callable, List, Optional, Set, Tuple, cast

import matplotlib.text
import matplotlib.ticker
import numpy as np
from PyQt6 import QtCore, QtWidgets

from ..functions import binary_search
from ..functions import formula as formula_func
from ..functions import peakfit as peakfit_func
from ..functions import spectrum as spectrum_func
from ..functions.peakfit import masslist as masslist_func
from ..models.spectrum.spectrum import (FittedPeak, MassListItem, Peak, PeakTags,
                                   Spectrum)
from ..utils.formula import Formula, formula_range
from . import PeakFitUi
from Orbitool import setting
from .component import Plot
from .manager import Manager, MultiProcess, state_node


class FitMethod(str, Enum):
    calc = "calc"
    mass_list = "mass list"


class Widget(QtWidgets.QWidget):
    show_spectrum = QtCore.pyqtSignal(Spectrum)
    show_masslist = QtCore.pyqtSignal()
    filter_selected = QtCore.pyqtSignal(bool)  # selected or unselected

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.ui = PeakFitUi.Ui_Form()
        self.setupUi()
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)
        manager.signals.peak_refit_finish.connect(self.peak_refit_finish)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start()
        self.plot_lim: Tuple[Tuple[int, int], Tuple[int, int]] = None

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.showSelectedPushButton.clicked.connect(self.showSelect)
        ui.toolBox.setCurrentIndex(0)

        # filters
        ui.filterSelectYToolButton.clicked.connect(self.filterSelected)
        ui.filterSelectNToolButton.clicked.connect(self.filterUnselected)
        ui.filterFormulaYToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_formula_y))
        ui.filterFormulaNToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_formula_n))
        ui.filterStableIsotopeYToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_stable_y))
        ui.filterStableIsotopeNToolButton.clicked.connect(
            lambda: self.filterGeneral(filter_stable_n))
        ui.filterTagYToolButton.clicked.connect(
            lambda: self.filter_tag(True))
        ui.filterTagNToolButton.clicked.connect(
            lambda: self.filter_tag(False))
        ui.filterIntensityMaxToolButton.clicked.connect(
            self.filter_intensity_max)
        ui.filterIntensityMinToolButton.clicked.connect(
            self.filter_intensity_min)
        ui.filterMassDefectToolButton.clicked.connect(
            self.filter_mass_defect)
        ui.filterGroupYToolButton.clicked.connect(
            self.filter_group_y)
        ui.filterGroupNToolButton.clicked.connect(
            self.filter_group_n)

        # step
        ui.stepAccordToMassCheckBox.toggled.connect(self.step_accord_toggled)
        ui.stepPushButton.clicked.connect(self.do_step)

        # clear
        ui.filterClearPushButton.clicked.connect(self.filterClear)

        # combox
        ui.filterTagComboBox.addItems([tag.name for tag in PeakTags])
        ui.addTagComboBox.addItems([tag.name for tag in PeakTags])
        ui.fitComboBox.addItem("calc", FitMethod.calc)
        ui.fitComboBox.addItem("mass list", FitMethod.mass_list)

        # actions
        ui.replotPushButton.clicked.connect(self.replot_within_peaks)
        ui.fitPushButton.clicked.connect(self.fit)
        ui.addTagPushButton.clicked.connect(self.add_tag)
        ui.actionAddToMassListPushButton.clicked.connect(self.addToMassList)
        ui.actionRmTagPushButton.clicked.connect(self.remove_tag)

        # plots
        self.plot = Plot(ui.widget)
        self.manager.bind.peak_fit_left_index.connect(
            "peakfit", self.move_plot_to_index)

        ui.scaleToSpectrumPushButton.clicked.connect(self.scale_spectrum)
        ui.yLogcheckBox.toggled.connect(self.ylog_toggle)
        ui.rescaleToolButton.clicked.connect(self.rescale_clicked)
        ui.leftToolButton.clicked.connect(lambda: self.moveRight(-1))
        ui.rightToolButton.clicked.connect(lambda: self.moveRight(1))
        ui.yLimDoubleToolButton.clicked.connect(lambda: self.y_times(2))
        ui.yLimHalfToolButton.clicked.connect(lambda: self.y_times(.5))

    def restore(self):
        self.show_and_plot()
        self.info.ui_state.restore_state(self.ui)

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    def show_and_plot(self):
        self.manager.signals.peak_list_show.emit()
        if self.info.spectrum:
            self.plot_peaks()

    @property
    def info(self):
        return self.manager.workspace.info.peak_fit_tab

    @state_node
    def showSelect(self):
        workspace = self.manager.workspace
        selected_index = self.manager.getters.spectra_list_selected_index.get()

        def read():
            spectrum = workspace.data.calibrated_spectra[selected_index]
            raw_peaks = spectrum_func.splitPeaks(
                spectrum.mz, spectrum.intensity)
            return spectrum, raw_peaks

        spectrum, raw_peaks = yield read, "read spectrum"
        raw_peaks: List[Peak]

        setting.set_global_val("multi-process-tmp-times", 20)
        raw_split_num, original_indexes, peaks = yield SplitPeaks(raw_peaks, func_kwargs={
            "func": workspace.info.peak_shape_tab.func}), "fit use peak shape func"

        peaks = cast(List[FittedPeak], peaks)
        manager = self.manager
        distribution = self.ui.calcDistributionCheckBox.isChecked()

        def formula_and_residual():
            rtol = workspace.info.formula_docker.calc_gen.rtol
            calc_get = workspace.info.formula_docker.get_calcer()

            for peak in manager.tqdm(peaks, msg="calc formulas"):
                peak.formulas = calc_get(peak.peak_position)
            if distribution:
                for peak in manager.tqdm(peaks, msg="correct formulas to natural distribution"):
                    peak.formulas = formula_func.correct_formula(peak, peaks, rtol)

            mz, residual = peakfit_func.calculateResidual(
                raw_peaks, original_indexes, peaks, workspace.info.peak_shape_tab.func)

            return mz, residual

        mz, residual = yield formula_and_residual, "calc formula"

        info = self.info
        info.spectrum, info.raw_peaks = spectrum, raw_peaks
        info.raw_split_num = raw_split_num
        info.original_indexes = original_indexes
        info.peaks = peaks
        info.shown_mz, info.shown_residual = info.residual_mz, info.residual_intensity = mz, residual
        info.shown_indexes = list(range(len(info.peaks)))
        info.shown_intensity = np.concatenate(
            [peak.intensity for peak in raw_peaks])

        self.show_spectrum.emit(info.spectrum)
        self.show_and_plot()

    def peak_refit_finish(self):
        self.manager.signals.peak_list_show.emit()

    def plot_peaks(self):
        info = self.info
        plot = self.plot
        is_log = self.ui.yLogcheckBox.isChecked()
        ax = plot.ax
        ax.clear()

        ax.axhline(color='k', linewidth=.5)
        ax.yaxis.set_tick_params(rotation=45)

        ax.set_yscale('log' if is_log else 'linear')
        if is_log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.plot(info.shown_mz, info.shown_intensity,
                color='k', linewidth=1, label="spectrum")
        ax.plot(info.shown_mz, info.shown_residual,
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
        if not self.ui.yLogcheckBox.isChecked():
            y_min = - 0.025 * y_max
        plot.ax.set_ylim(y_min, y_max)
        plot.canvas.draw()

    @state_node
    def rescale_clicked(self):
        self.rescale()
        self.plot.canvas.draw()

    def rescale(self):
        info = self.info
        mz = info.shown_mz
        intensity = info.shown_intensity
        if mz is None:
            return

        plot = self.plot
        x_min, x_max = plot.ax.get_xlim()
        id_min, id_max = binary_search.indexBetween_np(
            mz, (x_min, x_max))
        if id_min >= id_max:
            return
        y_max = intensity[id_min:id_max].max()

        if self.ui.yLogcheckBox.isChecked():
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
        info = self.info
        if info.spectrum is None:
            return
        spectrum = info.spectrum
        self.plot.ax.set_xlim(spectrum.mz.min(), spectrum.mz.max())

        self.rescale()

        self.plot.canvas.draw()

    def move_plot_to_index(self, index):
        peaks = self.info.peaks
        indexes = self.info.shown_indexes
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
        peaks = self.info.peaks
        indexes = self.info.shown_indexes

        index = binary_search.indexFirstBiggerThan(
            indexes, x_min, method=lambda indexes, ind: peaks[indexes[ind]].peak_position)

        self.manager.bind.peak_fit_left_index.emit_except("peakfit", index)
        self.plot_moved()

    def plot_moved(self):
        ax = self.plot.ax

        now_lim = (ax.get_xlim(), ax.get_ylim())
        self.plot_lim = now_lim

        info = self.info
        raw_peaks = info.raw_peaks
        original_indexes = info.original_indexes
        peaks = info.peaks
        indexes = info.shown_indexes

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
            if cnt == setting.peakfit.plot_show_formulas:
                break
        self.plot.canvas.draw()

    @state_node
    def filterClear(self):
        info = self.info
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
        info = self.info
        peaks = info.peaks
        info.shown_indexes = [
            index for index in info.shown_indexes if filter(peaks[index])]
        self.manager.signals.peak_list_show.emit()

    @state_node(withArgs=True)
    def filter_tag(self, y: bool):
        tag = self.ui.filterTagComboBox.currentText()
        tag: PeakTags = getattr(PeakTags, tag)
        if y:
            self._filter_general(lambda fp: tag.value in fp.tags)
        else:
            self._filter_general(lambda fp: tag.value not in fp.tags)

    @state_node
    def filter_intensity_max(self):
        value = self.ui.filterIntensityMaxDoubleSpinBox.value()
        self._filter_general(lambda fp: fp.peak_intensity < value)

    @state_node
    def filter_intensity_min(self):
        value = self.ui.filterIntensityMinDoubleSpinBox.value()
        self._filter_general(lambda fp: fp.peak_intensity > value)

    @state_node
    def filter_mass_defect(self):
        mi = self.ui.filterMassDefectMinDoubleSpinBox.value()
        ma = self.ui.filterMassDefectMaxDoubleSpinBox.value()
        self._filter_general(
            lambda fp: mi < fp.peak_position - round(fp.peak_position) < ma)

    @state_node
    def filter_group_y(self):
        group = self.ui.filterGroupLineEdit.text()
        group = Formula(group)
        self._filter_general(lambda fp: any(group in f for f in fp.formulas))

    @state_node
    def filter_group_n(self):
        group = self.ui.filterGroupLineEdit.text()
        group = Formula(group)
        self._filter_general(lambda fp: any(
            group not in f for f in fp.formulas))

    @state_node(withArgs=True)
    def generalAction(self, action: Callable[[FittedPeak], None], msg: str):
        yield from self._general_action(action, msg)

    def _general_action(self, action: Callable[[FittedPeak], None], msg: str):
        info = self.info

        peaks = info.peaks
        indexes = info.shown_indexes
        manager = self.manager
        if self.ui.onlySelectedCheckBox.isChecked():
            indexes = manager.getters.peak_list_selected_true_index.get()

        def func():
            for index in manager.tqdm(indexes):
                action(peaks[index])

        yield func, msg

        self.manager.signals.peak_list_show.emit()

    @state_node(mode='n', withArgs=True)
    def step_accord_toggled(self, value: bool):
        self.ui.stepRtolDoubleSpinBox.setEnabled(value)

    @state_node
    def do_step(self):
        ui = self.ui
        group_p = Formula(ui.stepPlusLineEdit.text())
        group_m = Formula(ui.stepMinusLineEdit.text())
        step_mi = ui.stepMinSpinBox.value()
        step_ma = ui.stepMaxSpinBox.value()
        mass = ui.stepAccordToMassCheckBox.isChecked()
        rtol = ui.stepRtolDoubleSpinBox.value() * 1e-6

        info = self.info
        peaks = info.peaks
        indexes = info.shown_indexes

        manager = self.manager

        if mass:
            def func():
                masses = []
                for index in indexes:
                    peak = peaks[index]
                    for f in peak.formulas:
                        masses.append(f.mass())
                masses = np.array(masses)
                rets = []
                mass_delta = group_p.mass() - group_m.mass()
                for index, peak in manager.tqdm(enumerate(peaks), "checking mass"):
                    for times in range(step_mi, step_ma + 1):
                        mass = peak.peak_position + mass_delta * times
                        if abs(mass / masses[binary_search.indexNearest_np(masses, mass)] - 1) < rtol:
                            rets.append(index)
                return rets
        else:
            def func():
                shown_sets: Set[Formula] = set()
                index: int
                for index in indexes:
                    peak = peaks[index]
                    for f in peak.formulas:
                        shown_sets.add(f)
                rets = []
                for index, peak in manager.tqdm(enumerate(peaks), "checking formula"):
                    for f in peak.formulas:
                        for ff in formula_range(f, group_p, group_m, step_mi, step_ma):
                            if ff in shown_sets:
                                rets.append(index)
                                break
                return rets
        rets: List[int] = yield func, "step"
        info.shown_indexes = rets
        self.manager.signals.peak_list_show.emit()

    @state_node
    def replot_within_peaks(self):
        info = self.info
        raw_peaks = info.raw_peaks
        o_peaks = info.peaks
        original_indexes = info.original_indexes
        indexes = info.shown_indexes
        func = self.manager.workspace.info.peak_shape_tab.func

        def residual():
            o_indexes = set(original_indexes[index] for index in indexes)
            peaks = [(index, peak) for index, peak in enumerate(
                o_peaks) if original_indexes[index] in o_indexes]
            o_indexes = sorted(o_indexes)
            r_peaks = [raw_peaks[index] for index in o_indexes]
            o_indexes = [original_indexes[index] for index, _ in peaks]
            peaks = [peak for _, peak in peaks]
            mz, residual = peakfit_func.calculateResidual(
                raw_peaks, o_indexes, peaks, func)

            intensity = np.concatenate([peak.intensity for peak in r_peaks])
            return mz, intensity, residual
        info.shown_mz, info.shown_intensity, info.shown_residual = yield residual, "calc residual"

        self.plot_peaks()

    @state_node
    def fit(self):
        method: FitMethod = self.ui.fitComboBox.currentData()
        if method == FitMethod.calc:
            yield from self.fit_formula()
        elif method == FitMethod.mass_list:
            yield from self.fit_mass_list()

    def fit_formula(self):
        info = self.info

        rtol = self.manager.workspace.info.formula_docker.calc_gen.rtol
        calc_get = self.manager.workspace.info.formula_docker.get_calcer()
        peaks = info.peaks
        indexes = info.shown_indexes
        ui = self.ui
        manager = self.manager

        if ui.onlySelectedCheckBox.isChecked():
            indexes = manager.getters.peak_list_selected_true_index.get()
        distribution = ui.calcDistributionCheckBox.isChecked()


        def func():
            index: int
            for index in manager.tqdm(indexes, msg="calc formula"):
                peak = peaks[index]
                peak.formulas = calc_get(peak.peak_position)


            if distribution:
                for index in manager.tqdm(indexes, msg="correct formulas to natural distribution"):
                    peak = peaks[index]
                    peak.formulas = formula_func.correct_formula(peak, peaks, rtol)

        yield func, "fit use calc"

        self.manager.signals.peak_list_show.emit()

    def fit_mass_list(self):
        rtol = self.manager.workspace.info.masslist_docker.rtol
        masslist = self.manager.workspace.info.masslist_docker.masslist

        def proc(fp: FittedPeak):
            fp.formulas = masslist_func.fitUseMassList(
                fp.peak_position, masslist, rtol)

        yield from self._general_action(proc, "fit use mass list")

    @state_node
    def add_tag(self):
        tag = self.ui.addTagComboBox.currentText()
        tag: PeakTags = getattr(PeakTags, tag)

        def proc(fp: FittedPeak):
            fp.tags = tag.value
        yield from self._general_action(proc, "add tag")

    @state_node
    def addToMassList(self):
        masslist = self.manager.workspace.info.masslist_docker.masslist
        rtol = self.manager.workspace.info.masslist_docker.rtol

        yield from self._general_action(lambda fp: masslist_func.addMassTo(
            masslist, MassListItem(fp.peak_position, fp.formulas), rtol=rtol), "add to mass list")

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
