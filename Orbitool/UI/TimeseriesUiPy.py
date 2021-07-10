from typing import Optional
from . import TimeseriesUi
from PyQt5 import QtWidgets

from .manager import Manager, state_node


class Widget(QtWidgets.QWidget, TimeseriesUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.inited_or_restored.connect(self.showSeries)

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
