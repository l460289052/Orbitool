from typing import Optional, Union
import matplotlib.ticker

from PyQt5 import QtCore, QtWidgets, QtGui

from ..functions import binary_search
from .component import Plot
import numpy as np
from .manager import Manager, state_node
from . import PeakFitFloatUi


class Window(QtWidgets.QMainWindow, PeakFitFloatUi.Ui_MainWindow):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, peak_index: int) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

        peaks = self.peakfit_info.peaks
        peak = peaks[peak_index]
        self.original_index = peak.original_index

        start = peak_index - 1
        while self.original_index == peaks[start]:
            start -= 1
        start += 1
        length = len(peaks)
        end = start + 1
        while end < length and self.original_index == peaks[end].original_index:
            end += 1
        self.peak_slice = slice(start, end)

        self.showPeak()
        self.plotPeak()

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        a0.accept()

    def setupUi(self, Form):
        super().setupUi(Form)
        self.plot = Plot(self.widget)

    @property
    def peakfit_info(self):
        return self.manager.workspace.peakfit_tab.info

    def showPeak(self):
        origin_peak = self.peakfit_info.raw_peaks[self.original_index]
        peaks = self.peakfit_info.peaks
        show_peaks = self.peakfit_info.peaks[self.peak_slice]

        table = self.peaksTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(show_peaks))

        rtol = self.manager.workspace.formula_docker.info.restricted_calc.rtol

        for index, peak in enumerate(show_peaks):
            def setItem(column, msg):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(msg)))

            setItem(0, format(peak.peak_position, '.5f'))
            setItem(1, ', '.join(str(f) for f in peak.formulas))
            setItem(2, format(peak.peak_intensity, '.5e'))
            setItem(4, format(peak.area, '.5e'))
            if len(peak.formulas) == 1:
                setItem(3,
                        format((peak.peak_position / peak.formulas[0].mass() - 1) * 1e6, '.5f'))
                formula = peak.formulas[0]
                if formula.isIsotope:
                    origin = formula.findOrigin()
                    mass = origin.mass()
                    d = mass * rtol
                    s = binary_search.indexBetween(
                        peaks, (mass - d, mass + d), method=(lambda peaks, index: peaks[index].peak_position))
                    for p in peaks[s]:
                        for f in p.formulas:
                            if f == origin:
                                setItem(5, format(peak.peak_intensity /
                                                  p.peak_intensity, '5f'))
                                setItem(
                                    6, format(formula.relativeAbundance(), '.5f'))
                                break
                        else:
                            continue
                        break

        table = self.intensityTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(origin_peak.mz))
        for index, (mz, intensity) in enumerate(zip(origin_peak.mz, origin_peak.intensity)):
            table.setItem(
                index, 0, QtWidgets.QTableWidgetItem(format(mz, '.5f')))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                format(intensity, '.5f')))

    def plotPeak(self):
        show_origin = self.originCheckBox.isChecked()
        show_sum = self.sumCheckBox.isChecked()
        show_id = self.idealCheckBox.isChecked()
        show_residual = self.residualCheckBox.isChecked()
        show_legend = self.legendCheckBox.isChecked()

        origin_peak = self.peakfit_info.raw_peaks[self.original_index]
        show_peaks = self.peakfit_info.peaks[self.peak_slice]

        func = self.manager.workspace.peak_shape_tab.info.func

        ax = self.plot.ax
        ax.clear()
        ax.axhline(color='k', linewidth=.5)

        if show_origin:
            ax.plot(origin_peak.mz, origin_peak.intensity,
                    label='origin', linewidth=2, color='k')

        id_mz = not show_id or np.arange(
            origin_peak.mz.min(), origin_peak.mz.max(), 2e-5)
        id_int = not show_id or np.zeros_like(id_mz)
        intensity_sum = not show_sum or np.zeros_like(origin_peak.intensity)
        intensity_diff = not show_residual or origin_peak.intensity.copy()

        for index, peak in enumerate(show_peaks):
            ax.plot(peak.mz, peak.intensity,
                    label=f"fitted peak {index}", linewidth=1.5)

            if show_id:
                id_int += func.getIntensity(id_mz, peak)

            if show_sum or show_residual:
                tmp_intensity = func.getIntensity(origin_peak.mz, peak)
                if show_sum:
                    intensity_sum += tmp_intensity
                if show_residual:
                    intensity_diff -= tmp_intensity

        if show_id:
            ax.plot(id_mz, id_int, label="ideal", color='g')

        if len(show_peaks) > 1:
            if show_sum:
                ax.plot(origin_peak.mz, intensity_sum,
                        label="fitted peak sum", linewidth=1.5)

        if show_residual:
            ax.plot(origin_peak.mz, intensity_diff,
                    label="peak residual", linewidth=1.5)

        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        if show_legend:
            ax.legend()

        ax.set_xlim(origin_peak.mz.min(), origin_peak.mz.max())
        self.plot.canvas.draw()
