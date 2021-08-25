import csv
from typing import Optional

from PyQt5 import QtWidgets

from ..utils.time_convert import getTimesExactToS
from . import TimeseriesUi
from .manager import Manager, state_node
from .utils import savefile


class Widget(QtWidgets.QWidget, TimeseriesUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.init_or_restored.connect(self.showSeries)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.exportPushButton.clicked.connect(self.export)

    @property
    def timeseries(self):
        return self.manager.workspace.timeseries_tab

    def showSeries(self):
        index = self.timeseries.info.show_index
        if index < 0:
            return
        series = self.timeseries.info.series[index]

        table = self.tableWidget
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
        index = self.timeseries.info.show_index
        if index < 0:
            return

        series = self.timeseries.info.series[index]
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
