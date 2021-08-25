import csv
from datetime import datetime, timedelta
from functools import partial
from itertools import chain
from typing import Dict, List, Optional, Tuple

import matplotlib.lines
import matplotlib.ticker
import numpy as np
from PyQt5 import QtCore, QtWidgets

from .. import config
from ..functions import binary_search
from ..functions.peakfit.base import BaseFunc as BaseFitFunc
from ..functions.spectrum import splitPeaks
from ..structures.HDF5 import StructureListView
from ..structures.spectrum import MassListItem, Spectrum
from ..structures.timeseries import TimeSeries
from ..utils.formula import Formula
from ..utils.time_convert import getTimesExactToS
from . import TimeseriesesUi
from .component import Plot, factory
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row, savefile


class Widget(QtWidgets.QWidget, TimeseriesesUi.Ui_Form):
    click_series = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

        self.shown_series: Dict[int, matplotlib.lines.Line2D] = {}

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = Plot(self.widget)

        self.calcPushButton.clicked.connect(self.calc)
        self.tableWidget.itemDoubleClicked.connect(self.seriesClicked)
        self.removeSelectedPushButton.clicked.connect(self.removeSelect)
        self.removeAllPushButton.clicked.connect(self.removeAll)
        self.exportPushButton.clicked.connect(self.export)

        self.rescalePushButton.clicked.connect(self.rescale)
        self.logScaleCheckBox.toggled.connect(self.logScale)

    @property
    def timeseries(self):
        return self.manager.workspace.timeseries_tab

    def restore(self):
        self.showTimeseries()
        self.timeseries.ui_state.set_state(self)

    def updateState(self):
        self.timeseries.ui_state.fromComponents(self, [
            self.mzRadioButton,
            self.mzDoubleSpinBox,
            self.formulaRadioButton,
            self.formulaLineEdit,
            self.mzRadioButton,
            self.mzMinDoubleSpinBox,
            self.mzMaxDoubleSpinBox,
            self.peakListRadioButton,
            self.massListRadioButton,
            self.selectedMassListRadioButton,
            self.rtolDoubleSpinBox,
            self.logScaleCheckBox])

    @state_node
    def calc(self):

        series: List[TimeSeries] = []
        rtol = self.rtolDoubleSpinBox.value() * 1e-6

        if self.mzRadioButton.isChecked():
            position = self.mzDoubleSpinBox.value()
            series.append(
                TimeSeries.FactoryPositionRtol(position, rtol, str(position)))
        elif self.formulaRadioButton.isChecked():
            f = Formula(self.formulaLineEdit.text())
            series.append(
                TimeSeries.FactoryPositionRtol(f.mass(), rtol, str(f)))
        elif self.mzRangeRadioButton.isChecked():
            l = self.mzMinDoubleSpinBox.value()
            r = self.mzMaxDoubleSpinBox.value()
            series.append(TimeSeries(
                position_min=l, position_max=r, tag="%.5f - %.5f" % (l, r)))
        elif self.peakListRadioButton.isChecked():
            peaklist = self.manager.workspace.peakfit_tab.info
            for index in peaklist.shown_indexes:
                peak = peaklist.peaks[index]
                if len(peak.formulas) == 1:
                    f = peak.formulas[0]
                    position = f.mass()
                    tag = str(f)
                else:
                    position = peak.peak_position
                    tag = format(position, '.5f')
                series.append(
                    TimeSeries.FactoryPositionRtol(position, rtol, tag))
        else:
            if self.selectedMassListRadioButton.isChecked():
                indexes = self.manager.getters.mass_list_selected_indexes.get()
                masslist = self.manager.workspace.masslist_docker.info.masslist
                masslist: List[MassListItem] = [masslist[index]
                                                for index in indexes]
            elif self.massListRadioButton.isChecked():
                masslist = self.manager.workspace.masslist_docker.info.masslist
            else:
                masslist = []
            for mass in masslist:
                if len(mass.formulas) == 1:
                    tag = str(mass.formulas[0])
                else:
                    tag = format(mass.position, '.5f')
                series.append(
                    TimeSeries.FactoryPositionRtol(mass.position, rtol, tag))

        func = self.manager.workspace.peak_shape_tab.info.func

        spectra = self.manager.workspace.calibration_tab.calibrated_spectra

        func_args = {"mz_range_list": [(s.position_min, s.position_max)
                                       for s in series], "func": func}

        write_args = {"series": series}

        series = yield CalcTimeseries(spectra, func_kwargs=func_args, write_kwargs=write_args), "calculate time series"

        info = self.timeseries.info
        info.series.extend(series)

        self.showTimeseries()

    def showTimeseries(self):
        series = self.timeseries.info.series

        table = self.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(series))
        shown_series = self.shown_series
        for index, s in enumerate(series):
            chb = factory.CheckBoxFactory(index in shown_series)
            chb.toggled.connect(partial(self.showTimeseriesAt, index))
            table.setCellWidget(index, 0, chb)
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(s.tag))
            table.setItem(index, 2, QtWidgets.QTableWidgetItem(
                format(s.position_min, '.5f')))
            table.setItem(index, 3, QtWidgets.QTableWidgetItem(
                format(s.position_max, '.5f')))

    @state_node(withArgs=True)
    def showTimeseriesAt(self, index: int, checked: bool):
        shown_series = self.shown_series
        ax = self.plot.ax
        if checked:
            if index in shown_series:
                return

            series = self.timeseries.info.series
            s = series[index]
            lines = ax.plot(s.times, s.intensity, label=s.tag)
            shown_series[index] = lines[-1]
        else:
            if index not in shown_series:
                return

            line = shown_series.pop(index)
            line.remove()

        ax.legend()
        self.plot.canvas.draw()

    @state_node(withArgs=True)
    def seriesClicked(self, item: QtWidgets.QTableWidgetItem):
        row = self.tableWidget.row(item)
        self.timeseries.info.show_index = row

        self.click_series.emit()

    @state_node
    def removeSelect(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        timeseries = self.timeseries.info.series
        for index in reversed(indexes):
            timeseries.pop(index)
        self.shown_series = {
            index - (index > indexes).sum(): line for index, line in self.shown_series.items()}
        self.showTimeseries()

    @state_node
    def removeAll(self):
        self.timeseries.info.series.clear()
        self.shown_series.clear()
        self.showTimeseries()
        self.plot.ax.clear()

    @state_node
    def export(self):
        series = self.timeseries.info.series
        if len(series) == 0 or all(len(s.times) == 0 for s in series):
            return
        time_min = min(min(s.times) for s in series if len(s.times) > 0)
        time_max = max(max(s.times) for s in series if len(s.times) > 0)

        ret, file = savefile("Timeseries", "CSV file(*.csv)",
                             f"timeseries {time_min.strftime(config.exportTimeFormat)}-{time_max.strftime(config.exportTimeFormat)}.csv")
        if not ret:
            return

        manager = self.manager

        def func():
            delta_time = timedelta(seconds=3)
            times = list(chain.from_iterable([s.times for s in series]))
            times.sort()
            last = times[-1]
            times = [time_a for time_a, time_b in zip(
                times, times[1:]) if time_b - time_a > delta_time]
            times.append(last)

            with open(file, 'w', newline='') as f:
                writer = csv.writer(f)
                row = ['isotime', 'igor time', 'matlab time', 'excel time']
                row.extend(s.tag for s in series)

                writer.writerow(row)

                indexes = np.zeros(len(series), dtype=int)
                max_indexes = np.array([len(s.times)
                                        for s in series], dtype=int)

                for current in manager.tqdm(times):
                    select = indexes < max_indexes
                    select &= np.array([slt and (abs(s.times[i] - current) < delta_time)
                                        for slt, i, s in zip(select, indexes, series)])
                    row = getTimesExactToS(current)
                    row.extend([s.intensity[i] if slt else '' for slt,
                                i, s in zip(select, indexes, series)])
                    indexes[select] += 1
                    writer.writerow(row)

        yield func

    @state_node(mode='x')
    def rescale(self):
        plot = self.plot
        series = self.timeseries.info.series
        if len(plot.ax.get_lines()) == 0:
            return
        l, r = plot.ax.get_xlim()
        l = np.array(matplotlib.dates.num2date(
            l).replace(tzinfo=None), dtype=np.datetime64)
        r = np.array(matplotlib.dates.num2date(
            r).replace(tzinfo=None), dtype=np.datetime64)
        b = 0
        t = 1
        shown_series = self.shown_series
        for index, s in enumerate(series):
            if index not in shown_series:
                continue
            sli = binary_search.indexBetween(s.times, (l, r))
            if sli.stop > sli.start:
                t = max(t, max(s.intensity[sli]))

        if self.logScaleCheckBox.isChecked():
            t *= 10
            b = 1
        else:
            delta = 0.05 * t
            b = -delta
            t += delta
        plot.ax.set_ylim(b, t)
        plot.canvas.draw()

    @state_node
    def logScale(self):
        log = self.logScaleCheckBox.isChecked()
        ax = self.plot.ax
        ax.set_yscale('log' if log else 'linear')
        if not log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        self.rescale()


class CalcTimeseries(MultiProcess):
    @staticmethod
    def read(file: StructureListView[Spectrum], **kwargs):
        for spectrum in file:
            yield spectrum

    @staticmethod
    def read_len(file: StructureListView[Spectrum], **kwargs) -> int:
        return len(file)

    @staticmethod
    def func(spectrum: Spectrum, func: BaseFitFunc, mz_range_list: List[Tuple[float, float]]):
        peaks = splitPeaks(spectrum.mz, spectrum.intensity)

        return spectrum.start_time, [func.fetchTimeseries(peaks, mi, ma) for mi, ma in mz_range_list]

    @staticmethod
    def write(file, rets, series: List[TimeSeries]):
        for time, ret in rets:
            for intensity, s in zip(ret, series):
                if intensity is not None:
                    s.times.append(time)
                    s.intensity.append(intensity)

        return series
