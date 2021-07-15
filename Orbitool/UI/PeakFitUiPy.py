from itertools import chain
from typing import Callable, List, Optional, Tuple, cast

from PyQt5 import QtCore, QtWidgets

from ..functions import formula as formula_func
from ..functions import peakfit as peakfit_func
from ..functions.peakfit import masslist as masslist_func
from ..functions import spectrum as spectrum_func
from ..structures.spectrum import FittedPeak, Peak, Spectrum, MassListItem
from . import PeakFitUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node


class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    show_spectrum = QtCore.pyqtSignal(Spectrum)
    show_peaklist = QtCore.pyqtSignal()
    show_masslist = QtCore.pyqtSignal()
    filter_selected = QtCore.pyqtSignal(bool)  # selected or unselected

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.inited_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

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

        self.previousShortCut = QtWidgets.QShortcut("Left", self)
        self.previousShortCut.activated.connect(lambda: self.moveRight(-1))
        self.nextShortCut = QtWidgets.QShortcut("Right", self)
        self.nextShortCut.activated.connect(lambda: self.moveRight(1))
        self.yDoubleShortCut = QtWidgets.QShortcut("Up", self)
        self.yDoubleShortCut.activated.connect(lambda: self.y_times(2))
        self.yHalfShortCut = QtWidgets.QShortcut("Down", self)
        self.yHalfShortCut.activated.connect(lambda: self.y_times(.5))

    def restore(self):
        self.show_and_plot()
        self.peakfit.ui_state.set_state(self)

    def updateState(self):
        self.peakfit.ui_state.fromComponents(self, [])

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
        selected_index = self.manager.fetch_func("spectra list select")()

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
    def calc_residual(self):
        info = self.peakfit.info
        func = self.manager.workspace.peak_shape_tab.info.func

        def calc():
            mz, residual = peakfit_func.calculateResidual(
                info.raw_peaks, info.original_indexes, info.peaks, func)
            return mz, residual

        info = self.peakfit.info
        info.residual_mz, info.residual_intensity = yield calc, "calculate residual"
        self.show_and_plot()

    def plot_peaks(self):
        info = self.peakfit.info
        plot = self.plot
        ax = plot.ax
        ax.clear()

        ax.axhline(color='k', linewidth=.5)
        ax.yaxis.set_tick_params(rotation=45)

        ax.plot(info.spectrum.mz, info.spectrum.intensity,
                color='k', linewidth=1, label="spectrum")
        ax.plot(info.residual_mz, info.residual_intensity,
                color='r', linewidth=.5, label="residual")
        ax.legend()

        mi = info.spectrum.mz.min()
        ma = info.spectrum.mz.max()
        ll, lr = ax.get_xlim()
        ax.set_xlim(mi if ll > mi else ll, ma if lr < ma else lr)

        plot.canvas.draw()

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
