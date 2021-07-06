from typing import Optional, List
from itertools import chain

from PyQt5 import QtCore, QtWidgets

from ..functions import(
    spectrum as spectrum_func,
    formula as formula_func,
    peakfit as peakfit_func)
from ..structures.spectrum import FittedPeak, Spectrum
from . import PeakFitUi
from .component import Plot
from .manager import Manager, state_node


class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    show_spectrum = QtCore.pyqtSignal(Spectrum)
    show_peaklist = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.showSelectedPushButton.clicked.connect(self.showSelect)
        self.plot = Plot(self.widget)

    @property
    def peakfit(self):
        return self.manager.workspace.peakfit_tab

    @state_node
    def showSelect(self):
        workspace = self.manager.workspace
        selected_index = workspace.spectra_list.info.selected_index or 0

        def read_split_fit_calc():
            spectrum = workspace.calibration_tab.calibrated_spectra[
                selected_index]
            raw_peaks = spectrum_func.splitPeaks(
                spectrum.mz, spectrum.intensity)
            peaks: List[FittedPeak] = []
            func = workspace.peak_shape_tab.info.func
            for index, peak in enumerate(raw_peaks):
                splited_peaks = func.splitPeak(peak)
                for p in splited_peaks:
                    p.original_index = index
                    peaks.append(p)
            calc = workspace.formula_docker.info.restricted_calc
            for peak in peaks:
                calc.get(peak.peak_position)

            for peak in peaks:
                peak.formulas = calc.get(peak.peak_position)
                peak.formulas = formula_func.correct(peak, peaks)

            mz, residual = peakfit_func.calculateResidual(
                raw_peaks, peaks, func)

            return spectrum, raw_peaks, peaks, (mz, residual)
        info = self.peakfit.info
        info.spectrum, info.raw_peaks, info.peaks, (info.residual_mz, info.residual_intensity) = yield read_split_fit_calc

        self.show_spectrum.emit(info.spectrum)
        self.show_peaklist.emit()
        self.plot_peaks()

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
