from typing import List, Optional, Union

import matplotlib.ticker
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from ..functions import binary_search
from ..functions import formula as formula_func
from ..structures.spectrum import FittedPeak
from ..utils.formula import Formula
from . import PeakFitFloatUi
from .component import Plot
from .manager import Manager, state_node


class Window(QtWidgets.QMainWindow, PeakFitFloatUi.Ui_MainWindow):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, peak_index: int) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

        info = self.peakfit_info
        original_indexes = info.original_indexes
        self.original_index = original_indexes[peak_index]

        start = peak_index - 1
        while self.original_index == original_indexes[start]:
            start -= 1
        start += 1
        length = len(original_indexes)
        end = start + 1
        while end < length and self.original_index == original_indexes[end]:
            end += 1
        self.original_slice = slice(start, end)
        self.peaks: List[FittedPeak] = info.peaks[start:end]

        self.showPeak()
        self.plotPeak()

    def setupUi(self, Form):
        super().setupUi(Form)
        self.plot = Plot(self.widget)
        self.refitPushButton.clicked.connect(self.refit)
        self.savePushButton.clicked.connect(self.save)
        self.closePushButton.clicked.connect(self.close)

    @property
    def peakfit_info(self):
        return self.manager.workspace.peakfit_tab.info

    def showPeak(self):
        origin_peak = self.peakfit_info.raw_peaks[self.original_index]
        peaks = self.peakfit_info.peaks
        show_peaks = self.peaks

        self.spinBox.setValue(len(show_peaks))

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
            table.setCellWidget(index, 1, QtWidgets.QLineEdit(
                ', '.join(str(f) for f in peak.formulas)))
            setItem(2, format(peak.peak_intensity, '.3e'))
            setItem(4, format(peak.area, '.3e'))
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
        show_peaks = self.peaks

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
                    label="peak residual", color='r', linewidth=1.5)

        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        if show_legend:
            ax.legend()

        ax.set_xlim(origin_peak.mz.min(), origin_peak.mz.max())
        self.plot.canvas.draw()

    @state_node
    def refit(self):
        num = self.spinBox.value()
        func = self.manager.workspace.peak_shape_tab.info.func
        info = self.peakfit_info
        fittedpeaks = func.splitPeak(
            info.raw_peaks[self.original_index], num, True)

        calc = self.manager.workspace.formula_docker.info.restricted_calc
        for peak in fittedpeaks:
            peak.original_index = self.original_index
            peak.formulas = calc.get(peak.peak_position)
            peak.formulas = formula_func.correct(peak, info.peaks)

        self.peaks = fittedpeaks

        self.showPeak()
        self.plotPeak()

    @state_node
    def save(self):
        table = self.peaksTableWidget
        new_peaks = self.peaks
        for index, peak in zip(range(table.rowCount()), new_peaks):
            formula_line_edit: QtWidgets.QLineEdit = table.cellWidget(index, 1)
            peak.formulas = [Formula(striped) for s in formula_line_edit.text(
            ).split(',') if len(striped := s.strip()) > 0]

        self.peakfit_info.raw_split_num[self.original_index] = len(new_peaks)

        peaks = self.peakfit_info.peaks
        original_indexes = self.peakfit_info.original_indexes
        shown_indexes = self.peakfit_info.shown_indexes

        start = self.original_slice.start
        stop = self.original_slice.stop
        delta = len(new_peaks) - stop + start

        del peaks[self.original_slice]
        for peak in reversed(new_peaks):
            peaks.insert(start, peak)

        del original_indexes[self.original_slice]
        for _ in range(len(new_peaks)):
            original_indexes.insert(start, self.original_index)

        i = binary_search.indexFirstNotSmallerThan(shown_indexes, start)
        j = binary_search.indexFirstNotSmallerThan(shown_indexes, stop)
        del shown_indexes[i:j]

        for j in range(len(new_peaks)):
            shown_indexes.insert(i + j, start + j)
        for j in range(i + len(new_peaks), len(shown_indexes)):
            shown_indexes[j] += delta

        self.callback.emit()
        self.close()
