from copy import deepcopy
import csv
from datetime import datetime, timedelta
from typing import List, Literal
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtWidgets import QWidget
import numpy as np

from Orbitool import setting
from Orbitool.UI import Manager
from Orbitool.structures.file import PeriodItem
from Orbitool.functions.file import generage_periods

from .CustomPeriodUi import Ui_Dialog
from .utils import str2timedelta, timedelta2str
from ..manager import state_node
from ..utils import openfile, savefile
from ..component import Plot


class Dialog(QtWidgets.QDialog):
    def __init__(
            self, manager: Manager,
            start_time: datetime, end_time: datetime,
            num_interval: int, time_interval: str,
            use: Literal["scan num", "minutes"]) -> None:
        super().__init__()
        self.manager = manager
        ui = self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.periods: List[PeriodItem] = deepcopy(
            self.manager.workspace.info.file_tab.periods)

        ui.startDateTimeEdit.setDateTime(start_time)
        ui.endDateTimeEdit.setDateTime(end_time)
        ui.numIntervalSpinBox.setValue(num_interval)
        ui.timeIntervalLineEdit.setText(time_interval)

        self.plot = Plot(self.ui.plotWidget, False)
        self.plot.ax.axis(False)
        self.ui.plotPositionHorizontalSlider.valueChanged.connect(
            self.refresh_plot)
        self.ui.plotFactorDoubleSpinBox.valueChanged.connect(self.refresh_plot)

        ui.generateTimePeriodPushButton.clicked.connect(
            self.generate_time_periods)
        ui.modifyStartPointsPushButton.clicked.connect(
            self.modify_start_points)
        ui.modifyEndPointsPushButton.clicked.connect(
            self.modify_end_points)
        ui.importPushButton.clicked.connect(self.import_periods)
        ui.exportPushButton.clicked.connect(self.export_periods)

        self.accepted.connect(self.update_periods)

        if self.periods is None:
            match use:
                case "scan num":
                    pass
                case "minutes":
                    self.periods = [
                        PeriodItem(s, e) for s, e in generage_periods(
                            start_time, end_time, str2timedelta(time_interval))]

        self.show_periods()

    @state_node(mode="e")
    def show_periods(self):
        table = self.ui.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(self.periods))

        for row, period in enumerate(self.periods):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(
                setting.format_time(period.start_time)))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(
                setting.format_time(period.end_time)))
        table.resizeColumnsToContents()

        self.plot_periods()

    def plot_periods(self):
        ax = self.plot.ax
        ax.cla()
        ax.axis(False)

        file_times = np.array(
            [(file.startDatetime, file.endDatetime)
             for file in self.manager.workspace.info.file_tab.pathlist], dtype='datetime64[s]')
        file_starts = file_times[:, 0]
        file_lengths = file_times[:, 1] - file_starts

        file_bar = ax.bar(
            file_starts, np.ones(len(file_starts)),
            file_lengths, np.zeros(len(file_starts)),
            color="#1f77b4", align='edge', edgecolor='k', linewidth=1.5,
            label="file")

        period_times = np.array(
            [(period.start_time, period.end_time)
             for period in self.periods], dtype='datetime64[s]')
        period_starts = period_times[:, 0]
        period_lengths = period_times[:, 1] - period_starts

        period_bar = ax.bar(
            period_starts, np.ones_like(period_starts, dtype=float) * 0.5,
            period_lengths, np.zeros_like(period_starts, dtype=float),
            color="#00cc00", align="edge", edgecolor='k', linewidth=1,
            label="period to average")
        ax.bar_label(period_bar, [timedelta2str(p.length())
                     for p in self.periods])

        for file, s, l in zip(self.manager.workspace.info.file_tab.pathlist, file_starts, file_lengths):
            ax.text(s, 1.1, setting.format_time(
                s.astype(datetime)), horizontalalignment="left")
            ax.text(s + l / 2, -0.2, file.path.replace("\\", "/").split("/")
                    [-1], verticalalignment="top", horizontalalignment="center")

        ax.set_ylim(-0.5, 2)
        self.plot_ref_length = file_lengths[0] * 1.7
        self.plot_left = file_starts[0] - self.plot_ref_length * 0.08
        self.plot_right = file_times[-1, -1] - self.plot_ref_length * 0.92
        self.plot_right = max(self.plot_left, self.plot_right)

        slider = self.ui.plotPositionHorizontalSlider
        slider.setRange(0, (self.plot_right - self.plot_left) //
                        self.plot_ref_length * 50+1)
        if slider.value() != 0:
            slider.setValue(0)
        else:
            self.refresh_plot()

        self.ui.plotPositionHorizontalSlider.setMinimum(0)
        ax.legend(loc="upper right", ncols=2, framealpha=0.5)

        self.plot.canvas.draw()

    @state_node(mode="e")
    def refresh_plot(self):
        left = self.plot_left + self.ui.plotPositionHorizontalSlider.value() / 50 * \
            self.plot_ref_length
        right = left + self.plot_ref_length / self.ui.plotFactorDoubleSpinBox.value()
        self.plot.ax.set_xlim(left, right)
        self.plot.canvas.draw()

    @state_node(mode="e")
    def generate_time_periods(self):
        ui = self.ui
        self.periods = [
            PeriodItem(s, e) for s, e in generage_periods(
                ui.startDateTimeEdit.dateTime().toPyDateTime(),
                ui.endDateTimeEdit.dateTime().toPyDateTime(),
                str2timedelta(ui.timeIntervalLineEdit.text())
            )]
        self.show_periods()

    def update_periods(self):
        self.manager.workspace.info.file_tab.periods = self.periods

    def get_modify_delta(self):
        s = self.ui.modifyLineEdit.text()
        t = -1 if s.startswith("-") else 1
        return str2timedelta(s.removeprefix("-")) * t

    @state_node(mode="e")
    def modify_start_points(self):
        delta = self.get_modify_delta()
        last = None
        new_periods = deepcopy(self.periods)
        for period in new_periods:
            if period.start_time is not None:
                period.start_time += delta
                assert period.start_time < period.end_time
                if last:
                    assert period.start_time > last.end_time
                last = period
        self.periods = new_periods
        self.show_periods()

    @state_node(mode="e")
    def modify_end_points(self):
        delta = self.get_modify_delta()
        last = None
        new_periods = deepcopy(self.periods)
        for period in new_periods:
            if period.end_time is not None:
                period.end_time += delta
                assert period.start_time < period.end_time
                if last:
                    assert period.start_time > last.end_time
                last = period
        self.periods = new_periods
        self.show_periods()

    @state_node(mode="e")
    def import_periods(self):
        success, file = openfile(
            "Select one period file", "CSV files(*.csv)")
        if not success:
            return

        def func():
            ret = []
            with open(file, 'r') as f:
                reader = csv.reader(f)
                it = iter(reader)
                next(it)  # skip row
                for row in it:
                    if row[0]:
                        times = (setting.parse_time(
                            row[0]), setting.parse_time(row[1]))
                    else:
                        times = (None, None)
                    if len(row) == 4:
                        nums = (int(row[2]), int(row[3]))
                    else:
                        nums = ()
                    item = PeriodItem(*(times + nums))
                    ret.append(item)
            return ret
        self.periods = yield func, "Read periods"
        self.show_periods()

    @state_node(mode="e")
    def export_periods(self):
        success, file = savefile("Save to", "CSV files(*.csv)")
        if not success:
            return

        periods = self.periods

        def func():
            with open(file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(
                    ('start time', 'end time', 'start num', 'end num'))
                for p in periods:
                    if p.start_time:
                        writer.writerow(
                            (setting.format_time(p.start_time), setting.format_time(p.end_time), -1, -1))
                    else:
                        writer.writerow(("", "", p.start_num, p.end_num))

        yield func, "exporting periods"
