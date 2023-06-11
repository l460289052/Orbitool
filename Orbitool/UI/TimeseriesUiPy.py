import csv
from typing import Optional

from PyQt5 import QtWidgets

from ..utils.time_format.time_convert import getTimesExactToS
from . import TimeseriesUi
from .manager import Manager, state_node
from .utils import savefile


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.ui = TimeseriesUi.Ui_Form()
        self.setupUi()
        manager.init_or_restored.connect(self.showSeries)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.exportPushButton.clicked.connect(self.export)

    @property
    def info(self):
        return self.manager.workspace.info.time_series_tab

    def showSeries(self):
        index = self.info.show_index
        if index < 0:
            return
        series = self.manager.workspace.data.time_series[index]

        table = self.ui.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(series.times))

        for index, (time, intensity) in enumerate(zip(series.times, series.intensity)):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(
                time.isoformat(sep=' ')))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                format(intensity, '.5f')))

    @state_node
    def export(self):
        index = self.info.show_index
        if index < 0:
            return

        series = self.manager.workspace.data.time_series[index]
        ret, f = savefile("timeseries", "CSV file(*.csv)",
                          f"timeseries {series.tag}")
        if not ret:
            return

        def func():
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(
                    ['isotime', 'igor time', 'matlab time', 'excel time', 'intensity'])
                for time, intensity in zip(series.times, series.intensity):
                    row = getTimesExactToS(time)
                    row.append(intensity)
                    writer.writerow(row)

        yield func
