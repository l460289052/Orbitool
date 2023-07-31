from typing import List, Optional, Union
from copy import deepcopy

import matplotlib.ticker
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from ..functions import binary_search
from ..functions.peakfit import get_peak_position
from ..functions import formula as formula_func
from ..structures.spectrum import FittedPeak
from ..utils.formula import Formula
from . import PeakFitFloatUi
from .component import Plot
from .manager import Manager, state_node
from .utils import set_header_sizes
from .formulas import FormulaResultWindow


class Window(QtWidgets.QMainWindow):
    callback = QtCore.pyqtSignal()

    @classmethod
    def get_or_create(cls, manager: Manager, peak_index: int):
        info = manager.workspace.info.peak_fit_tab
        original_index = info.original_indexes[peak_index]
        wins = manager.peak_float_wins
        if original_index in wins:
            win = wins[original_index]
        else:
            win = cls(manager, original_index)
            wins[original_index] = win
        return win

    def __init__(self, manager: Manager, original_index: int) -> None:
        super().__init__()
        self.manager = manager
        self.ui = PeakFitFloatUi.Ui_MainWindow()
        self.setupUi()

        info = self.info
        self.original_index = original_index

        self.original_slice = binary_search.indexBetween(
            info.original_indexes, (original_index, original_index))
        self.original_peaks = info.peaks[self.original_slice]
        self.peaks: List[FittedPeak] = deepcopy(self.original_peaks)

        self.showPeak()
        self.plotPeak()

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)
        self.plot = Plot(ui.widget)
        ui.refitPushButton.clicked.connect(self.refit)
        ui.savePushButton.clicked.connect(self.save)
        ui.closePushButton.clicked.connect(self.close)

        ui.sumCheckBox.clicked.connect(self.replotPeak)
        ui.idealCheckBox.clicked.connect(self.replotPeak)
        ui.legendCheckBox.clicked.connect(self.replotPeak)
        ui.originCheckBox.clicked.connect(self.replotPeak)
        ui.residualCheckBox.clicked.connect(self.replotPeak)
        set_header_sizes(ui.peaksTableWidget.horizontalHeader(),
                         [140, 300, 130, 130, 130, 130, 130])

        ui.peaksTableWidget.itemDoubleClicked.connect(self.finetuneFormula)

    def set_formulas(self, peak_index: int, formulas: List[Formula]):
        ind: int = peak_index - self.original_slice.start
        self.peaks[ind].formulas = formulas
        self.showPeak()

    @property
    def info(self):
        return self.manager.workspace.info.peak_fit_tab

    @state_node(withArgs=True)
    def finetuneFormula(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        peak_index = self.original_slice.start + row

        manager = self.manager
        if manager.formulas_result_win is not None:
            manager.formulas_result_win.close()
            del manager.formulas_result_win
        manager.formulas_result_win = FormulaResultWindow.fromFittedPeak(
            manager, peak_index)
        manager.formulas_result_win.show()
        manager.formulas_result_win.acceptSignal.connect(
            lambda formulas: self.finetuneFinish(row, formulas))

    def finetuneFinish(self, local_index: int, formulas: List[Formula]):
        self.peaks[local_index].formulas = formulas
        self.showPeak()

    def showPeak(self):
        origin_peak = self.info.raw_peaks[self.original_index]
        peaks = self.info.peaks
        show_peaks = self.peaks

        ui = self.ui
        ui.spinBox.setValue(len(show_peaks))

        table = ui.peaksTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(show_peaks))

        rtol = self.manager.workspace.info.formula_docker.calc_gen.rtol

        for index, peak in enumerate(show_peaks):
            def setText(column, msg):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(msg)))

            setText(0, format(peak.peak_position, '.5f'))
            setText(1, ', '.join(str(f) for f in self.original_peaks[binary_search.indexNearest(
                self.original_peaks, peak.peak_position, method=get_peak_position)].formulas))
            setText(2, ', '.join(str(f) for f in peak.formulas))
            setText(3, format(peak.peak_intensity, '.3e'))
            setText(5, format(peak.area, '.3e'))
            if len(peak.formulas) == 1:
                setText(4,
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
                                setText(6, format(peak.peak_intensity /
                                                  p.peak_intensity, '5f'))
                                setText(
                                    7, format(formula.relativeAbundance(), '.5f'))
                                break
                        else:
                            continue
                        break

        table = ui.intensityTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(origin_peak.mz))
        for index, (mz, intensity) in enumerate(zip(origin_peak.mz, origin_peak.intensity)):
            table.setItem(
                index, 0, QtWidgets.QTableWidgetItem(format(mz, '.5f')))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                format(intensity, '.5f')))

    def plotPeak(self):
        ui = self.ui
        show_origin = ui.originCheckBox.isChecked()
        show_sum = ui.sumCheckBox.isChecked()
        show_id = ui.idealCheckBox.isChecked()
        show_residual = ui.residualCheckBox.isChecked()
        show_legend = ui.legendCheckBox.isChecked()

        origin_peak = self.info.raw_peaks[self.original_index]
        show_peaks = self.peaks

        func = self.manager.workspace.info.peak_shape_tab.func

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
    def replotPeak(self):
        self.plotPeak()

    @state_node
    def refit(self):
        num = self.ui.spinBox.value()
        func = self.manager.workspace.info.peak_shape_tab.func
        info = self.info
        fittedpeaks = func.splitPeak(
            info.raw_peaks[self.original_index], num, True)

        calc_get = self.manager.workspace.info.formula_docker.get_calcer()
        for peak in fittedpeaks:
            peak.formulas = calc_get(peak.peak_position)
            # peak.formulas = formula_func.correct(peak, info.peaks)

        self.peaks = fittedpeaks

        self.showPeak()
        self.plotPeak()

    @state_node
    def save(self):
        new_peaks = self.peaks

        self.info.raw_split_num[self.original_index] = len(new_peaks)

        peaks = self.info.peaks
        original_indexes = self.info.original_indexes
        shown_indexes = self.info.shown_indexes

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

        self.manager.signals.peak_refit_finish.emit()
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.manager.peak_float_wins.pop(self.original_index, None)
        a0.accept()
