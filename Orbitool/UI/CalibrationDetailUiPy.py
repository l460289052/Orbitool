import math

import numpy as np
from .manager import Manager, state_node
import matplotlib.ticker


from PyQt6 import QtWidgets, QtGui
from Orbitool.models.spectrum import Spectrum, safeCutSpectrum, safeSplitSpectrum
from . import CalibrationDetailUi
from .component import Plot


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager

        ui = self.ui = CalibrationDetailUi.Ui_Form()
        ui.setupUi(self)
        self.spectrum_plot = Plot(ui.spectrumPlotWidget)
        self.filePlot = Plot(ui.filePlotWidget)

        ui.spectraTableWidget.itemDoubleClicked.connect(self.showSpectrumAt)
        ui.spectrumIonsTableWidget.itemDoubleClicked.connect(self.showIonAt)
        ui.filesTableWidget.itemDoubleClicked.connect(self.showFileAt)

        self.spectrum: Spectrum = None
        self.inner_index: int = None

        self.init()

        self.current_ion_index: int = None

        self.previousIonsShortCut = QtGui.QShortcut("Left", self)
        self.previousIonsShortCut.activated.connect(lambda: self.next_ion(-1))
        self.nextIonShortCut = QtGui.QShortcut("Right", self)
        self.nextIonShortCut.activated.connect(lambda: self.next_ion(1))

    @property
    def info(self):
        return self.manager.workspace.info.calibration_tab

    def init(self):
        workspace = self.manager.workspace
        info = self.info

        spectrum_infos = workspace.info.noise_tab.denoised_spectrum_infos
        table = self.ui.spectraTableWidget
        table.clearContents()
        table.setRowCount(len(spectrum_infos))
        for row, spectrum_info in enumerate(spectrum_infos):
            item = QtWidgets.QTableWidgetItem(
                "{!s} -> {!s}".format(spectrum_info.start_time, spectrum_info.end_time))
            table.setItem(row, 0, item)

        paths = list(info.calibrator_segments.keys())
        table = self.ui.filesTableWidget
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
        info = self.info
        if not info.path_ion_infos:
            return
        spectrum = self.manager.workspace.data.raw_spectra[index]

        ion_infos = info.path_ion_infos[spectrum.path]
        inner_index = index
        # to find current spectrum corresponding ion-infos and inner-index
        for ion_info in info.path_ion_infos.values():
            if ion_info:
                i = next(iter(ion_info.values()))
                if inner_index < len(i.raw_position):
                    break
                inner_index -= len(i.raw_position)
            else:
                break

        self.spectrum = spectrum
        self.inner_index = index
        self.current_ion_index = None

        table = self.ui.spectrumIonsTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(info.last_ions))
        table.setVerticalHeaderLabels(
            [ion.shown_text for ion in info.last_ions])

        color = QtGui.QColor(0xB6EEA6)

        plot = self.spectrum_plot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=.5)

        ax.plot(spectrum.mz, spectrum.intensity, color='red', label="raw")

        if True:
            cali_mz = []
            for mz_part, calibrator in zip(
                    safeSplitSpectrum(
                        spectrum.mz, spectrum.intensity, 
                        np.array([info.end_point for info in info.last_calibrate_info_segments])),
                    info.calibrator_segments[spectrum.path]):
                cali_mz.append(calibrator.calibrate_mz(mz_part))
            cali_mz = np.concatenate(cali_mz)
            ax.plot(cali_mz, spectrum.intensity, color='black', label="calibrated")

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
            ax.plot([position, position], [0, intensity], color="blue")
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
    def showIonAt(self, item: QtWidgets.QTableWidgetItem):
        self.showIon(item.row())

    @state_node(withArgs=True)
    def next_ion(self, step: int):
        if self.spectrum is None:
            return
        if self.current_ion_index is None:
            self.showIon(0)
        else:
            self.showIon((self.current_ion_index + step) % len(self.info.ions))

    def showIon(self, index: int):
        self.current_ion_index = index
        ion_info = self.info.path_ion_infos[self.spectrum.path][self.info.ions[index].formula]
        ion_position = ion_info.raw_position[self.inner_index]
        ion_intensity = ion_info.raw_intensity[self.inner_index]

        x_min = ion_position - .1
        x_max = ion_position + .1
        y_min = -ion_intensity * .1
        y_max = ion_intensity * 1.2

        plot = self.spectrum_plot
        ax = plot.ax
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        plot.canvas.draw()

    @state_node(withArgs=True)
    def showFileAt(self, item: QtWidgets.QTableWidgetItem):
        self.showFile(item.row())

    def showFile(self, index: int):
        info = self.info
        if not info.calibrator_segments:
            return
        path = list(info.calibrator_segments.keys())[index]

        ion_infos = info.path_ion_infos[path]

        table = self.ui.fileIonsTableWidget
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

        for cali_info in info.last_calibrate_info_segments:
            if cali_info.end_point is not math.inf:
                ax.axvline(cali_info.end_point, color='blue')

        formula_info = self.manager.workspace.info.formula_docker
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
