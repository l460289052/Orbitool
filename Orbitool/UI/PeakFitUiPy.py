from itertools import chain
from typing import Callable, List, Optional, Tuple

from PyQt5 import QtCore, QtWidgets

from ..functions import formula as formula_func
from ..functions import peakfit as peakfit_func
from ..functions import spectrum as spectrum_func
from ..structures.spectrum import FittedPeak, Peak, Spectrum
from . import PeakFitUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node


class SplitPeaks(MultiProcess):
    @staticmethod
    def read(raw_peaks: List[Peak], **kwargs):
        for index, peak in enumerate(raw_peaks):
            yield index, peak

    @staticmethod
    def func(data: Tuple[int, Peak], func: peakfit_func.BaseFunc):
        index, peak = data
        split_peaks = func.splitPeak(peak)
        for p in split_peaks:
            p.original_index = index
        return split_peaks

    @staticmethod
    def write(file, rets):
        return list(chain.from_iterable(rets))


class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    show_spectrum = QtCore.pyqtSignal(Spectrum)
    show_peaklist = QtCore.pyqtSignal()
    filter_selected = QtCore.pyqtSignal(bool)  # selected or unselected

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.inited_or_restored.connect(self.show_and_plot)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.showSelectedPushButton.clicked.connect(self.showSelect)
        self.filterSelectedPushButton.clicked.connect(self.filterSelected)
        self.filterUnselectedPushButton.clicked.connect(self.filterUnselected)
        self.filterFormulaWithPushButton.clicked.connect(self.filterFormula)
        self.filterFormulaWithoutPushButton.clicked.connect(
            self.filterFormulaWithout)
        self.filterClearPushButton.clicked.connect(self.filterClear)
        self.plot = Plot(self.widget)

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
        selected_index = workspace.spectra_list.info.selected_index or 0

        def read():
            spectrum = workspace.calibration_tab.calibrated_spectra[
                selected_index]
            raw_peaks = spectrum_func.splitPeaks(
                spectrum.mz, spectrum.intensity)
            return spectrum, raw_peaks

        spectrum, raw_peaks = yield read

        peaks: List[FittedPeak] = yield SplitPeaks(raw_peaks, func_kwargs={
            "func": workspace.peak_shape_tab.info.func})

        def formula_and_residual():
            calc = workspace.formula_docker.info.restricted_calc
            for peak in peaks:
                calc.get(peak.peak_position)

            for peak in peaks:
                peak.formulas = calc.get(peak.peak_position)
                peak.formulas = formula_func.correct(peak, peaks)

            mz, residual = peakfit_func.calculateResidual(
                raw_peaks, peaks, workspace.peak_shape_tab.info.func)

            return mz, residual

        mz, residual = yield formula_and_residual

        info = self.peakfit.info
        info.spectrum, info.raw_peaks = spectrum, raw_peaks
        info.peaks = peaks
        info.residual_mz, info.residual_intensity = mz, residual
        info.shown_indexes = list(range(len(info.peaks)))

        self.show_spectrum.emit(info.spectrum)
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
