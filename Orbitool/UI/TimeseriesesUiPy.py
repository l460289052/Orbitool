import csv
from datetime import datetime, timedelta
from functools import partial
from itertools import chain
from typing import Dict, Iterable, List, Literal, Optional, Tuple

import matplotlib.lines
import matplotlib.ticker
import numpy as np
from PyQt6 import QtCore, QtWidgets

from .. import setting
from ..functions import binary_search
from ..functions.peakfit.base import BaseFunc as BaseFitFunc
from ..functions.peakfit import NoFitFunc
from ..functions.spectrum import splitPeaks, safeCutSpectrum
from ..structures.HDF5 import StructureListView
from ..structures.spectrum import MassListItem, Spectrum
from ..structures.timeseries import TimeSeries
from ..workspace.timeseries import TimeSeriesInfoRow
from ..utils.formula import Formula
from ..utils.time_format.time_convert import getTimesExactToS, converters
from . import TimeseriesesUi
from .component import Plot, factory
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row, savefile


class Widget(QtWidgets.QWidget):
    click_series = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.ui = TimeseriesesUi.Ui_Form()
        self.setupUi()
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

        self.shown_series: Dict[int, matplotlib.lines.Line2D] = {}

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)
        ui.toolBox.setCurrentIndex(0)

        self.plot = Plot(ui.widget)

        ui.calcPeakPushButton.clicked.connect(self.calc_peak)
        ui.calcRangePushButton.clicked.connect(self.calc_sum)

        ui.tableWidget.itemDoubleClicked.connect(self.seriesClicked)
        ui.removeSelectedPushButton.clicked.connect(self.removeSelect)
        ui.removeAllPushButton.clicked.connect(self.removeAll)
        ui.exportTimeseriesPushButton.clicked.connect(
            lambda: self.export("intensity"))
        ui.exportDeviationPushButton.clicked.connect(
            lambda: self.export("deviation"))

        ui.rescalePushButton.clicked.connect(self.rescale)
        ui.logScaleCheckBox.toggled.connect(self.logScale)

    @property
    def info(self):
        return self.manager.workspace.info.time_series_tab

    @property
    def timeseries(self):
        return self.manager.workspace.data.time_series

    def restore(self):
        for func, msg in self.showTimeseries():
            func()
        self.info.ui_state.restore_state(self.ui)

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    @state_node
    def calc_peak(self):
        ui = self.ui

        series: List[TimeSeries] = []
        rtol = ui.rtolDoubleSpinBox.value() * 1e-6

        if ui.mzRadioButton.isChecked():
            position = ui.mzDoubleSpinBox.value()
            series.append(
                TimeSeries.FactoryPositionRtol(position, rtol))
        elif ui.formulaRadioButton.isChecked():
            f = Formula(ui.formulaLineEdit.text())
            series.append(
                TimeSeries.FactoryPositionRtol(f.mass(), rtol, [f]))
        elif ui.peakListRadioButton.isChecked():
            peaklist = self.manager.workspace.info.peak_fit_tab
            index: int
            for index in peaklist.shown_indexes:
                peak = peaklist.peaks[index]
                if len(peak.formulas) == 1:
                    f = peak.formulas[0]
                    position = f.mass()
                else:
                    position = peak.peak_position
                series.append(
                    TimeSeries.FactoryPositionRtol(position, rtol, peak.formulas))
        else:
            if ui.selectedMassListRadioButton.isChecked():
                indexes = self.manager.getters.mass_list_selected_indexes.get()
                masslist = self.manager.workspace.info.masslist_docker.masslist
                masslist: List[MassListItem] = [masslist[index]
                                                for index in indexes]
            elif ui.massListRadioButton.isChecked():
                masslist = self.manager.workspace.info.masslist_docker.masslist
            else:
                masslist = []
            for mass in masslist:
                series.append(
                    TimeSeries.FactoryPositionRtol(mass.position, rtol, mass.formulas))

        func = self.manager.workspace.info.peak_shape_tab.func

        spectra = self.manager.workspace.data.calibrated_spectra

        position_list = [(s.position_min, s.position_max) for s in series]
        position_min = min(p for p, _ in position_list)
        position_max = max(p for _, p in position_list)
        func_args = {"mz_range_list": position_list, "mz_cut": (
            position_min, position_max), "func": func}

        write_args = {"series": series}

        series = yield CalcTimeseries(spectra, func_kwargs=func_args, write_kwargs=write_args), "calculate time series"

        yield partial(self.timeseries.extend, series), "write to disk"
        self.info.timeseries_infos.extend(
            TimeSeriesInfoRow.FromTimeSeries(s) for s in series)

        yield from self.showTimeseries()

    @state_node
    def calc_sum(self):
        ui = self.ui

        mz_min = ui.rangeMinDoubleSpinBox.value()
        mz_max = ui.rangeMaxDoubleSpinBox.value()

        series = TimeSeries(mz_min, mz_max, True)

        spectra = self.manager.workspace.data.calibrated_spectra

        target = setting.timeseries.mz_sum_target
        match setting.timeseries.mz_sum_func:
            case "nofit":
                func = NoFitFunc()
            case "norm":
                func = self.manager.workspace.info.peak_shape_tab.func
        func_args = {
            "target": target,
            "func": func,
            "mz_range": (mz_min, mz_max)
        }
        write_args = {"series": series}

        series = yield CalcSumTimeSeries(spectra, func_kwargs=func_args, write_kwargs=write_args), "calculate mz range sum series"

        self.timeseries.append(series)
        self.info.timeseries_infos.append(
            TimeSeriesInfoRow.FromTimeSeries(series))

        yield from self.showTimeseries()

    def showTimeseries(self):
        if len(self.info.timeseries_infos) != len(self.timeseries):
            def func():
                self.info.timeseries_infos = [
                    TimeSeriesInfoRow.FromTimeSeries(s) for s in self.timeseries]
            yield func, "update timeseries info"

        table = self.ui.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(self.info.timeseries_infos))
        shown_series = self.shown_series
        for index, s in enumerate(self.info.timeseries_infos):
            chb = factory.CheckBox(index in shown_series)
            chb.toggled.connect(partial(self.showTimeseriesAt, index))
            table.setCellWidget(index, 0, chb)
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(s.get_name()))
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

            s = self.timeseries[index]
            i = self.info.timeseries_infos[index]
            kwds = {}
            if len(s.times) == 1:
                kwds["marker"] = '.'
            lines = ax.plot(s.times, s.intensity, label=i.get_name(), **kwds)
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
        row = item.row()
        self.info.show_index = row

        self.click_series.emit()

    @state_node
    def removeSelect(self):
        indexes = get_tablewidget_selected_row(self.ui.tableWidget)
        timeseries = self.timeseries
        infos = self.info.timeseries_infos
        for index in reversed(indexes):
            del infos[index]
            del timeseries[index]
        self.shown_series = {
            index - (index > indexes).sum(): line for index, line in self.shown_series.items()}
        yield from self.showTimeseries()

    @state_node
    def removeAll(self):
        self.info.timeseries_infos.clear()
        self.timeseries.clear()
        self.shown_series.clear()
        yield from self.showTimeseries()
        self.plot.ax.clear()

    @state_node(withArgs=True)
    def export(self, target: Literal["intensity", "deviation"]):
        infos = self.info.timeseries_infos
        series = self.timeseries
        if len(infos) == 0 or all(info.time_min == 0 for info in infos):
            return
        time_min = min(info.time_min for info in infos if info.time_min)
        time_max = max(info.time_max for info in infos if info.time_max)

        ret, file = savefile("Timeseries", "CSV file(*.csv)",
                             f"timeseries {target} {time_min.strftime(setting.general.export_time_format)}-{time_max.strftime(setting.general.export_time_format)}.csv")
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

            stimes: List[np.ndarray] = []
            svalues: List[np.ndarray] = []
            for s in series:
                stimes.append(s.times)
                match target:
                    case "intensity":
                        svalues.append(s.intensity)
                    case "deviation":
                        deviation = s.get_deviations()
                        if len(deviation) == 0 and len(s.times) > 0:
                            deviation = [""] * len(s.times)
                        svalues.append(deviation)

            formats = setting.timeseries.export_time_formats
            time_formats = {k: v for k, (v, _) in converters.items() if k in formats}
            with open(file, 'w', newline='') as f:
                writer = csv.writer(f)
                row = [f"{time} time" for time in time_formats.keys()]

                row.extend(i.get_name() for i in infos)

                writer.writerow(row)

                indexes = np.zeros(len(infos), dtype=int)
                max_indexes = np.array([len(t) for t in stimes], dtype=int)

                for current in manager.tqdm(times):
                    select = indexes < max_indexes
                    select &= np.array([slt and (abs(s[i] - current) < delta_time)
                                        for slt, i, s in zip(select, indexes, stimes)])

                    prt_time = current.replace(microsecond=0)
                    row = [converter(prt_time)
                           for converter in time_formats.values()]
                    row.extend([(v[i] if slt else '')
                               for slt, i, v in zip(select, indexes, svalues)])

                    indexes[select] += 1
                    writer.writerow(row)

        yield func

    @state_node(mode='x')
    def rescale(self):
        plot = self.plot
        series = self.timeseries
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
        for index in shown_series:
            s = series[index]
            sli = binary_search.indexBetween(s.times, (l, r))
            if sli.stop > sli.start:
                t = max(t, max(s.intensity[sli]))

        if self.ui.logScaleCheckBox.isChecked():
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
        log = self.ui.logScaleCheckBox.isChecked()
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
    def func(spectrum: Spectrum, func: BaseFitFunc, mz_range_list: List[Tuple[float, float]], mz_cut: Tuple[float, float]):
        mz, intensity = safeCutSpectrum(
            spectrum.mz, spectrum.intensity, *mz_cut)

        peaks = splitPeaks(mz, intensity)

        return spectrum.start_time, [func.get_peak_max(peaks, mi, ma) for mi, ma in mz_range_list]

    @staticmethod
    def write(file, rets: Iterable[Tuple[datetime, Iterable[Tuple[float, float]]]], series: List[TimeSeries]):
        for time, ret in rets:
            for r, s in zip(ret, series):
                if r is not None:
                    position, intensity = r
                    s.append(time, intensity, position)

        return series


class CalcSumTimeSeries(MultiProcess):
    @staticmethod
    def read(file: StructureListView[Spectrum], **kwargs):
        yield from file

    @staticmethod
    def read_len(file: StructureListView[Spectrum], **read_kwargs) -> int:
        return len(file)

    @staticmethod
    def func(spectrum: Spectrum, func: BaseFitFunc, mz_range: Tuple[float, float], target: str):
        mz, intensity = safeCutSpectrum(
            spectrum.mz, spectrum.intensity, *mz_range)
        peaks = splitPeaks(mz, intensity)

        return spectrum.start_time, func.get_peak_sum(peaks, target)

    @staticmethod
    def write(file, rets: Iterable[Tuple[datetime, float]], series: TimeSeries):
        for dt, s in rets:
            series.append(dt, s)
        return series
