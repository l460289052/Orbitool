from ast import mod
from copy import deepcopy
import csv
from datetime import datetime, timedelta
from typing import List, Literal, Union
import weakref
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtWidgets import QStyleOptionViewItem, QWidget
import numpy as np

from Orbitool import setting
from Orbitool.UI import Manager
from Orbitool.structures.file import PeriodItem
from Orbitool.functions.file import generage_periods, generate_num_periods, get_num_range_from_ranges

from .CustomPeriodUi import Ui_Dialog
from .utils import str2timedelta, timedelta2str
from ..manager import state_node
from ..utils import openfile, savefile
from ..component import Plot


class Dialog(QtWidgets.QDialog):
    def __init__(
            self, manager: Manager,
            start_time: datetime, end_time: datetime,
            num_interval: int, time_interval: str) -> None:
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
        ui.tableWidget.setItemDelegate(
            TableEditDelegate(ui.tableWidget, weakref.ref(self)))
        ui.plotPositionHorizontalSlider.valueChanged.connect(
            self.refresh_plot)
        ui.plotFactorDoubleSpinBox.valueChanged.connect(self.refresh_plot)
        ui.plotHideLabelCheckBox.toggled.connect(self.plot_periods)

        ui.generateNumPeriodPushButton.clicked.connect(
            self.generate_num_periods)
        ui.generateTimePeriodPushButton.clicked.connect(
            self.generate_time_periods)
        ui.modifyStartPointsPushButton.clicked.connect(
            self.modify_start_points)
        ui.modifyEndPointsPushButton.clicked.connect(
            self.modify_end_points)
        ui.importPushButton.clicked.connect(self.import_periods)
        ui.exportPushButton.clicked.connect(self.export_periods)

        self.accepted.connect(self.update_periods)

    @property
    def paths(self):
        return self.manager.workspace.info.file_tab.pathlist.paths

    def init_periods(self, start_time, end_time, time_interval):
        if self.periods is None:
            self.periods = [
                PeriodItem(s, e) for s, e in generage_periods(
                    start_time, end_time, str2timedelta(time_interval))]

    def show_periods(self):
        table = self.ui.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(self.periods))

        for row, period in enumerate(self.periods):
            if period.start_time:
                a = setting.format_time(period.start_time)
                b = setting.format_time(period.end_time)
            else:
                a = str(period.start_num)
                b = str(period.stop_num)
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(a))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(b))
        table.resizeColumnsToContents()

        self.plot_periods()

    @state_node(mode="e")
    def plot_periods(self):
        ax = self.plot.ax
        ax.cla()
        ax.axis(False)

        plot_time = all(p.start_time is not None for p in self.periods)
        plot_num = all(p.start_num >= 0 for p in self.periods)

        if not plot_time and not plot_num:
            return

        if plot_time:
            file_times = np.array(
                [(file.startDatetime, file.endDatetime)
                 for file in self.paths], dtype='datetime64[s]')
            file_starts = file_times[:, 0]
            file_lengths = file_times[:, 1] - file_starts
            file_start_label = list(
                map(setting.format_time, file_starts.astype(datetime)))

            period_times = np.array(
                [(period.start_time, period.end_time)
                 for period in self.periods], dtype='datetime64[s]')
            period_starts = period_times[:, 0]
            period_lengths = period_times[:, 1] - period_starts

            period_label = [
                f"length:{timedelta2str(l)}" for l in period_lengths.astype(timedelta)]

        if plot_num:
            file_lengths = np.array(
                [file.scanNum for file in self.paths], dtype=int)
            file_starts = file_lengths.cumsum()
            file_starts[1:] = file_starts[:-1]
            file_starts[0] = 0

            file_start_label = [
                f"file start scan num:{s}" for s in file_starts]

            period_nums = np.array([(p.start_num, p.stop_num)
                                   for p in self.periods], dtype=int)
            period_starts = period_nums[:, 0]
            period_lengths = period_nums[:, 1] - period_starts

            period_label = [f"length:{l}" for l in period_lengths]

        file_bar = ax.bar(
            file_starts, np.ones(len(file_starts)),
            file_lengths, np.zeros(len(file_starts)),
            color="#1f77b4", align='edge', edgecolor='k', linewidth=1.5,
            label="file")
        period_bar = ax.bar(
            period_starts, np.ones_like(period_starts, dtype=float) * 0.5,
            period_lengths, np.zeros_like(period_starts, dtype=float),
            color="#00cc00", align="edge", edgecolor='k', linewidth=1,
            label="period to average")

        hide_label = self.ui.plotHideLabelCheckBox.isChecked()
        if not hide_label:
            ax.bar_label(period_bar, period_label)
            ax.bar_label(period_bar, [
                f"{i}-th" for i in range(1, len(period_starts) + 1)], label_type="center")

            for file, label, s, l in zip(self.paths, file_start_label, file_starts, file_lengths):
                ax.text(s, 1.1, label, horizontalalignment="left")
                ax.text(s + l / 2, -0.15, f"file:{file.get_show_name()}",
                        verticalalignment="top", horizontalalignment="center")

        ax.set_ylim(-0.5, 2.2)
        self.plot_ref_length = file_lengths[0] * 1.7
        self.plot_left = file_starts[0] - self.plot_ref_length * 0.08
        self.plot_right = file_starts[-1] + \
            file_lengths[-1] - self.plot_ref_length * 0.92
        self.plot_right = max(self.plot_left, self.plot_right)

        slider = self.ui.plotPositionHorizontalSlider
        slider.setRange(0, int((self.plot_right - self.plot_left) /
                        self.plot_ref_length * 50 + 1))
        if slider.value() != 0:
            slider.setValue(0)
        else:
            self.refresh_plot()

        self.ui.plotPositionHorizontalSlider.setMinimum(0)
        if not hide_label:
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
    def generate_num_periods(self):
        ui = self.ui
        if not self.paths:
            return
        tr = (
            ui.startDateTimeEdit.dateTime().toPyDateTime(),
            ui.endDateTimeEdit.dateTime().toPyDateTime()
        )
        N = ui.numIntervalSpinBox.value()

        def update_scan_num():
            for p in self.paths:
                if p.scanNum < 0:
                    p.scanNum = p.getFileHandler().totalScanNum
            start_scan_num, stop_scan_num, total_scan_num = get_num_range_from_ranges(
                (p.getFileHandler() for p in self.paths), tr)
            return [PeriodItem(start_num=a, stop_num=b) for a, b in generate_num_periods(
                start_scan_num, stop_scan_num, N)]
        periods = yield update_scan_num, "update scan num"

        self.periods = periods

        self.show_periods()

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
        s = s.removeprefix("-")
        if s.isnumeric():
            return int(s) * t
        return str2timedelta(s) * t

    @state_node(mode="e")
    def modify_start_points(self):
        delta = self.get_modify_delta()
        period: PeriodItem
        last_time: PeriodItem = None
        last_num: PeriodItem = None
        new_periods = deepcopy(self.periods)
        for period in new_periods:
            if period.start_time is not None:
                period.start_time += delta
                assert period.start_time < period.end_time
                if last_time:
                    assert period.start_time > last_time.end_time
                last_time = period
            elif period.start_num >= 0:
                period: PeriodItem
                period.start_num += delta
                assert period.start_num < period.stop_num
                if last_num:
                    assert period.start_num > last_num.stop_num
                last_num = period

        self.periods = new_periods
        self.show_periods()

    @state_node(mode="e")
    def modify_end_points(self):
        delta = self.get_modify_delta()
        period: PeriodItem
        last_time: PeriodItem = None
        last_num: PeriodItem = None
        new_periods = deepcopy(self.periods)
        for period in new_periods:
            if period.end_time is not None:
                period.end_time += delta
                assert period.start_time < period.end_time
                if last_time:
                    assert period.start_time > last_time.end_time
                last_time = period
            elif period.stop_num >= 0:
                period: PeriodItem
                period.stop_num += delta
                assert period.start_num < period.stop_num
                if last_num:
                    assert period.start_num > last_num.stop_num
                last_num = period
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
                        writer.writerow(("", "", p.start_num, p.stop_num))

        yield func, "exporting periods"


class TableEditDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent, dialog: weakref.ReferenceType[Dialog]) -> None:
        super().__init__(parent)
        self.dialog_ref = dialog

    @property
    def paths(self):
        return self.dialog_ref().paths

    @property
    def periods(self):
        return self.dialog_ref().periods

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QtCore.QModelIndex) -> QWidget:
        periods = self.periods
        period = periods[index.row()]
        if period.start_num >= 0:
            sb = QtWidgets.QSpinBox(parent)
            match index.column():
                case 0:
                    sb.setRange(
                        0 if index.row() == 0 else self.periods[index.row() - 1].stop_num, period.stop_num - 1)
                case 1:
                    sb.setRange(
                        period.start_num + 1,
                        sum(p.scanNum for p in self.paths) if index.row() == len(
                            self.periods) - 1 else self.periods[index.row() + 1].start_num)
            return sb
        de = QtWidgets.QDateTimeEdit(parent)
        match index.column():
            case 0:
                if index.row():
                    de.setMinimumDateTime(
                        self.periods[index.row() - 1].end_time)
                de.setMaximumDateTime(period.end_time)
            case 1:
                de.setMinimumDateTime(period.start_time)
                if index.row() < len(periods) - 1:
                    de.setMaximumDateTime(periods[index.row() + 1].start_time)
        return de

    def setEditorData(self, editor: Union[QtWidgets.QSpinBox, QtWidgets.QDateTimeEdit], index: QtCore.QModelIndex) -> None:
        period = self.periods[index.row()]
        if period.start_num >= 0:
            match index.column():
                case 0:
                    editor.setValue(period.start_num)
                case 1:
                    editor.setValue(period.stop_num)
        match index.column():
            case 0:
                editor.setDateTime(period.start_time)
            case 1:
                editor.setDateTime(period.end_time)

    def setModelData(self, editor: Union[QtWidgets.QSpinBox, QtWidgets.QDateTimeEdit], model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        period = self.periods[index.row()]
        if period.start_num >= 0:
            value = editor.value()
            match index.column():
                case 0:
                    period.start_num = value
                case 1:
                    period.stop_num = value
            model.setData(index, str(value))
        else:
            value = editor.dateTime().toPyDateTime()
            match index.column():
                case 0:
                    period.start_time = value
                case 1:
                    period.end_time = value
            model.setData(index, setting.format_time(value))

        self.dialog_ref().plot_periods()
