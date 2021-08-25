from itertools import chain
from typing import Callable, List, Optional, Tuple, cast

from PyQt5 import QtCore, QtWidgets
import matplotlib.ticker
import matplotlib.text
import numpy as np

from ..functions import formula as formula_func, peakfit as peakfit_func, binary_search
from ..functions.peakfit import masslist as masslist_func
from ..functions import spectrum as spectrum_func
from ..structures.spectrum import FittedPeak, Peak, Spectrum, MassListItem
from . import PeakFitUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node


class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    show_spectrum = QtCore.pyqtSignal(Spectrum)
    show_peaklist = QtCore.pyqtSignal()
    peaklist_left = QtCore.pyqtSignal(float)
    show_masslist = QtCore.pyqtSignal()
    filter_selected = QtCore.pyqtSignal(bool)  # selected or unselected

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start()
        self.plot_lim: Tuple[Tuple[int, int], Tuple[int, int]] = None

    def setupUi(self, Form):
        super().setupUi(Form)

        self.showSelectedPushButton.clicked.connect(self.showSelect)
        self.filterSelectedPushButton.clicked.connect(self.filterSelected)
        self.filterUnselectedPushButton.clicked.connect(self.filterUnselected)
        self.filterFormulaWithPushButton.clicked.connect(self.filterFormula)
        self.filterFormulaWithoutPushButton.clicked.connect(
            self.filterFormulaWithout)
        self.filterClearPushButton.clicked.connect(self.filterClear)

        self.actionFit_FormulaPushButton.clicked.connect(self.fitFormula)
        self.actionFit_ForceFormulaPushButton.clicked.connect(
            self.fitForceFormula)
        self.actionFit_MassListPushButton.clicked.connect(self.fitMassList)
        self.actionAddToMassListPushButton.clicked.connect(self.addToMassList)
        self.actionRmPushButton.clicked.connect(self.removeFromPeaks)

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
        self.show_peaklist.emit()
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
            for peak in manager.tqdm(peaks, msg="init formula"):
                calc.get(peak.peak_position)

            for peak in manager.tqdm(peaks):
                peak.formulas = calc.get(peak.peak_position)
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

    @state_node(mode='x')
    def peak_refit_finish(self):
        info = self.peakfit.info
        func = self.manager.workspace.peak_shape_tab.info.func

        def calc():
            mz, residual = peakfit_func.calculateResidual(
                info.raw_peaks, info.original_indexes, info.peaks, func)
            return mz, residual

        info = self.peakfit.info
        info.residual_mz, info.residual_intensity = yield calc, "calculate residual"

        ax = self.plot.ax
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        self.show_and_plot()
        ax = self.plot.ax
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

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

    @state_node(withArgs=True)
    def moveRight(self, step):
        plot = self.plot
        x_min, x_max = plot.ax.get_xlim()
        plot.ax.set_xlim(x_min + step, x_max + step)
        self.plot.canvas.draw()

    @state_node(withArgs=True)
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

        peak = peaks[indexes[index]]
        new_x_min = peak.mz.min()
        x_min, x_max = ax.get_xlim()
        new_x_max = new_x_min + (x_max - x_min)
        ax.set_xlim(new_x_min, new_x_max)

        self.plot_moved()

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
        self.show_peaklist.emit()

    @state_node
    def filterFormula(self):
        info = self.peakfit.info
        peaks = info.peaks
        info.shown_indexes = [
            index for index in info.shown_indexes if len(peaks[index].formulas) > 0]
        self.show_peaklist.emit()

    @state_node
    def filterFormulaWithout(self):
        info = self.peakfit.info
        peaks = info.peaks
        info.shown_indexes = [
            index for index in info.shown_indexes if len(peaks[index].formulas) == 0]
        self.show_peaklist.emit()

    @state_node
    def filterSelected(self):
        self.filter_selected.emit(True)
        self.show_peaklist.emit()

    @state_node
    def filterUnselected(self):
        self.filter_selected.emit(False)
        self.show_peaklist.emit()

    @state_node
    def fitFormula(self):
        info = self.peakfit.info

        calc = self.manager.workspace.formula_docker.info.restricted_calc
        peaks = info.peaks
        indexes = info.shown_indexes

        manager = self.manager

        def func():
            for peak in manager.tqdm(peaks, msg="init formula"):
                calc.get(peak.peak_position)  # init
            for index in manager.tqdm(indexes):
                peak = peaks[index]
                peak.formulas = calc.get(peak.peak_position)
                peak.formulas = formula_func.correct(peak, peaks, calc.rtol)

        yield func, "fit use restricted calc"

        self.show_peaklist.emit()

    @state_node
    def fitForceFormula(self):
        info = self.peakfit.info

        calc = self.manager.workspace.formula_docker.info.force_calc
        peaks = info.peaks
        indexes = info.shown_indexes

        manager = self.manager

        def func():
            for index in manager.tqdm(indexes):
                peak = peaks[index]
                peak.formulas = calc.get(peak.peak_position)

        yield func, "fit use unrestricted calc"

        self.show_peaklist.emit()

    @state_node
    def fitMassList(self):
        info = self.peakfit.info

        rtol = self.manager.workspace.masslist_docker.info.rtol
        masslist = self.manager.workspace.masslist_docker.info.masslist
        peaks = info.peaks
        indexes = info.shown_indexes

        def func():
            for index in indexes:
                peak = peaks[index]
                peak.formulas = masslist_func.fitUseMassList(
                    peak.peak_position, masslist, rtol)

        yield func, "fit use mass list"

        self.show_peaklist.emit()

    @state_node
    def addToMassList(self):
        info = self.peakfit.info

        masslist = self.manager.workspace.masslist_docker.info.masslist
        rtol = self.manager.workspace.masslist_docker.info.rtol
        peaks = info.peaks
        indexes = info.shown_indexes

        def func():
            for index in indexes:
                peak = peaks[index]
                masslist_func.addMassTo(
                    masslist,
                    MassListItem(position=peak.peak_position,
                                 formulas=peak.formulas),
                    rtol=rtol)

        yield func, "add to mass list"

        self.show_masslist.emit()

    @state_node
    def removeFromPeaks(self):
        info = self.peakfit.info

        peaks = info.peaks
        original_indexes = info.original_indexes
        indexes = info.shown_indexes

        def func():
            indexes.reverse()
            for index in indexes:
                peaks.pop(index)
                original_indexes.pop(index)
            info.shown_indexes = list(range(len(peaks)))

        yield func, "remove"

        self.show_peaklist


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
