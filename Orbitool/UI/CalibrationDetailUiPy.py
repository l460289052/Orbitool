from cProfile import label
import math

import numpy as np
from .manager import Manager, state_node
import matplotlib.ticker


from PyQt5 import QtWidgets, QtGui
from . import CalibrationDetailUi
from .component import Plot


class Widget(QtWidgets.QWidget, CalibrationDetailUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.spectrumPlot = Plot(self.spectrumPlotWidget)
        self.filePlot = Plot(self.filePlotWidget)

        self.spectraTableWidget.itemDoubleClicked.connect(self.showSpectrumAt)
        self.filesTableWidget.itemDoubleClicked.connect(self.showFileAt)

        self.init()

    def info(self):
        return self.manager.workspace.calibration_tab.info

    def init(self):
        workspace = self.manager.workspace
        info = self.info()

        spectrum_infos = workspace.noise_tab.info.denoised_spectrum_infos
        table = self.spectraTableWidget
        table.clearContents()
        table.setRowCount(len(spectrum_infos))
        for row, spectrum_info in enumerate(spectrum_infos):
            item = QtWidgets.QTableWidgetItem(
                "{!s} -> {!s}".format(spectrum_info.start_time, spectrum_info.end_time))
            table.setItem(row, 0, item)

        paths = list(info.calibrator_segments.keys())
        table = self.filesTableWidget
        table.clearContents()
        table.setRowCount(len(paths))
        for row, path in enumerate(paths):
            table.setItem(
                row, 0,
                QtWidgets.QTableWidgetItem(str(info.path_times[path])))
            table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(path))

        self.showSpcetrum(0)
        self.showFile(0)

    @state_node(withArgs=True)
    def showSpectrumAt(self, item: QtWidgets.QTableWidgetItem):
        index = item.row()
        self.showSpcetrum(index)

    def showSpcetrum(self, index: int):
        info = self.info()
        if not info.path_ion_infos:
            return
        spectrum = self.manager.workspace.noise_tab.raw_spectra[index]

        ion_infos = info.path_ion_infos[spectrum.path]
        calibrators = info.calibrator_segments[spectrum.path]
        inner_index = index
        for cali in info.calibrator_segments.values():
            if inner_index < len(cali[0].formulas):
                break
            inner_index -= len(cali[0].formulas)

        table = self.spectrumIonsTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(info.last_ions))
        table.setVerticalHeaderLabels(
            [ion.shown_text for ion in info.last_ions])

        color = QtGui.QColor(0xB6EEA6)

        plot = self.spectrumPlot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=.5)
        ax.plot(spectrum.mz, spectrum.intensity, color='black')

        for index, (ion, used) in enumerate(info.yield_ion_used(spectrum.path)):
            formula = ion.formula
            if used:
                def setItem(column, text):
                    item = QtWidgets.QTableWidgetItem(text)
                    item.setBackground(color)
                    table.setItem(index, column, item)
            else:
                def setItem(column, text):
                    table.setItem(
                        index, column, QtWidgets.QTableWidgetItem(text))
            ion_info = ion_infos[formula]
            position = ion_info.raw_position[inner_index]
            intensity = ion_info.raw_intensity[inner_index]
            setItem(0, format(position, '.5f'))
            setItem(1, format((1 - formula.mass() / position) * 1e6, '.5f'))
            setItem(2, format(intensity, '.3e'))

            if math.isnan(position):
                continue
            ax.plot([position, position], [0, intensity], color='r')
            if used:
                ax.annotate(ion.shown_text, (position, intensity), color='g')
            else:
                ax.annotate(ion.shown_text, (position, intensity))

        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.legend()
        ax.relim()
        ax.autoscale_view(True, True, True)
        plot.canvas.draw()

    @state_node(withArgs=True)
    def showFileAt(self, item: QtWidgets.QTableWidgetItem):
        self.showFile(item.row())

    def showFile(self, index: int):
        info = self.info()
        if not info.calibrator_segments:
            return
        path = list(info.calibrator_segments.keys())[index]

        ion_infos = info.path_ion_infos[path]

        table = self.fileIonsTableWidget
        table.setRowCount(0)
        table.setRowCount(len(ion_infos))
        color = QtGui.QColor(0xB6EEA6)
        used_points = []
        unused_points = []
        for index, (ion, used) in enumerate(info.yield_ion_used(path)):
            ion_info = ion_infos[ion.formula]
            if used:
                def setItem(column, s):
                    item = QtWidgets.QTableWidgetItem(s)
                    item.setBackground(color)
                    table.setItem(index, column, item)
                used_points.append((ion_info.position, ion_info.rtol))
            else:
                def setItem(column, s):
                    table.setItem(index, column, QtWidgets.QTableWidgetItem(s))
                unused_points.append((ion_info.position, ion_info.rtol))
            setItem(0, format(ion.formula.mass(), '.5f'))
            setItem(1, format(ion_info.position, '.5f'))
            setItem(2, format(ion_info.rtol * 1e6, '.5f'))
            setItem(3, str(used))

        plot = self.filePlot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=.5)

        formula_info = self.manager.workspace.formula_docker.info
        start_point = formula_info.mz_min
        for cali_info, cali in zip(info.last_calibrate_info_segments, info.calibrator_segments[path]):
            x = np.linspace(start_point, min(
                cali_info.end_point, formula_info.mz_max), 1000)
            y = cali.predict_rtol(x) * 1e6
            ax.plot(x, y, color="black")
            start_point = cali_info.end_point

        used_points = np.array(used_points).reshape(-1, 2)
        unused_points = np.array(unused_points).reshape(-1, 2)
        ax.scatter(used_points[:, 0], used_points[:, 1] * 1e6, c='green')
        ax.scatter(unused_points[:, 0], unused_points[:, 1] * 1e6, c='red')

        ax.set_ylabel('rtol(ppm)')
        ax.set_xlim(formula_info.mz_min, formula_info.mz_max)
        plot.canvas.draw()
