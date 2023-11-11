import csv
from typing import Optional

from PyQt6 import QtWidgets

from ..utils.time_format.time_convert import converters
from . import TimeseriesUi
from .manager import Manager, state_node
from .utils import savefile
from Orbitool import setting


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.ui = TimeseriesUi.Ui_Form()
        self.setupUi()
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.retentionTimeCheckBox.stateChanged.connect(self.retention_time_toggle)
        ui.exportPushButton.clicked.connect(self.export)

    @property
    def info(self):
        return self.manager.workspace.info.time_series_tab

    def restore(self):
        self.info.ui_state.restore_state(self.ui)
        self.showSeries()

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    @state_node
    def retention_time_toggle(self):
        self.showSeries()

    def showSeries(self):
        index = self.info.show_index
        if index < 0:
            return
        retention_time = self.ui.retentionTimeCheckBox.isChecked()
        series = self.manager.workspace.data.time_series[index]

        table = self.ui.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(series.times))

        if not self.info.timeseries_infos[index].valid():
            return

        positions = series.positions
        deviation = series.get_deviations()
        begin = series.times[0]
        for index, (time, intensity) in enumerate(zip(series.times, series.intensity)):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(
                str(time-begin) if retention_time else
                time.strftime(setting.general.time_format) ))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                format(intensity, '.3e')))
            if positions:
                table.setItem(index, 2, QtWidgets.QTableWidgetItem(
                    format(positions[index], '.5f')))
                table.setItem(index, 3, QtWidgets.QTableWidgetItem(
                    format(deviation[index], '.3f')))
    
    @state_node(mode='e')
    def showSeries_CatchException(self):
        self.showSeries()

    @state_node
    def export(self):
        index = self.info.show_index
        if index < 0:
            return

        info = self.info.timeseries_infos[index]
        series = self.manager.workspace.data.time_series[index]
        ret, f = savefile("timeseries", "CSV file(*.csv)",
                          f"timeseries {info.get_name()}")
        if not ret:
            return

        def func():
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                formats = setting.timeseries.export_time_formats
                time_formats = {k: v for k,
                                (v, _) in converters.items() if k in formats}
                row = [f"{time} time" for time in time_formats.keys()]
                row.extend(["intensity", "position", "deviation"])
                writer.writerow(row)
                length = len(series.times)
                for time, *row in zip(
                        series.times, series.intensity,
                        series.positions or [""] * length,
                        series.get_deviations() or [""] * length):
                    prt_time = time.replace(microsecond=0)
                    writer.writerow([c(prt_time)
                                    for c in time_formats.values()] + row)

        yield func
