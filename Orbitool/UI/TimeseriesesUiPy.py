import csv
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from itertools import chain

from PyQt5 import QtWidgets, QtCore
import numpy as np

from ..functions.peakfit.base import BaseFunc as BaseFitFunc
from ..functions.spectrum import splitPeaks
from ..structures.HDF5 import StructureListView
from ..structures.spectrum import MassListItem, Spectrum
from ..structures.timeseries import TimeSeries
from ..utils.formula import Formula
from ..utils.time_convert import getTimesExactToS
from . import TimeseriesesUi
from .component import Plot
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row, savefile
from .. import config


class Widget(QtWidgets.QWidget, TimeseriesesUi.Ui_Form):
    click_series = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.inited_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = Plot(self.widget)

        self.calcPushButton.clicked.connect(self.calc)
        self.tableWidget.itemDoubleClicked.connect(self.seriesClicked)
        self.exportPushButton.clicked.connect(self.export)

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
            self.exportWithPpmCheckBox,
            self.legendsCheckBox,
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
                indexes = self.manager.fetch_func("mass list select")()
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
        for index, s in enumerate(series):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(s.tag))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                format(s.position_min, '.5f')))
            table.setItem(index, 2, QtWidgets.QTableWidgetItem(
                format(s.position_max, '.5f')))

        ax = self.plot.ax
        ax.clear()
        for s in series:
            ax.plot(s.times, s.intensity, label=s.tag)

        ax.legend()

        self.plot.canvas.draw()

    @state_node(withArgs=True)
    def seriesClicked(self, item: QtWidgets.QTableWidgetItem):
        row = self.tableWidget.row(item)
        self.timeseries.info.show_index = row

        self.click_series.emit()

    @state_node
    def export(self):
        series = self.timeseries.info.series
        if len(series) == 0:
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
