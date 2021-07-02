from typing import Union, Optional
import numpy as np
from . import CalibrationInfoUi
from .manager import Manager
from PyQt5 import QtWidgets, QtCore


class Widget(QtWidgets.QWidget, CalibrationInfoUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        manager.inited.connect(self.showAllInfo)

    @property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    @property
    def plot(self):
        return self.manager.calibrationPlot

    def showAllInfo(self):
        table = self.tableWidget
        table.clearContents()

        info = self.calibration.info

        table.setColumnCount(len(info.ions))
        hlables = [ion.shown_text for ion in info.ions]
        table.setHorizontalHeaderLabels(hlables)

        table.setRowCount(len(info.calibrators))
        if len(info.calibrators) == 0:
            return

        calibrators = sorted(info.calibrators.values(),
                             key=lambda calibrator: calibrator.time)

        times = []
        devitions = []
        for row, calibrator in enumerate(calibrators):
            times.append(calibrator.time)

            for column, rtol in enumerate(calibrator.ions_rtol):
                table.setItem(row, column, QtWidgets.QTableWidgetItem(
                    format(rtol * 1e6, ".5f")))
            devitions.append(calibrator.ions_rtol)
        vlabels = [time.replace(microsecond=0).isoformat(
            sep=' ')[:-3] for time in times]

        table.setVerticalHeaderLabels(vlabels)

        devitions = np.array(devitions)

        plot = self.plot

        ax = plot.ax
        ax.clear()
        ax.axhline(color="k", linewidth=.5)

        if len(devitions) > 0:
            for index in range(devitions.shape[1]):
                ax.plot(times, devitions[:, index],
                        label=info.ions[index].shown_text)

        ax.set_xlabel("starting time")
        ax.set_ylabel("Deviation (ppm)")
        ax.legend()
        ax.relim()
        ax.autoscale(True, True, True)
        plot.canvas.draw()
