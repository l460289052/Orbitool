import csv
import math
from copy import copy
from typing import List, Optional, Tuple, Union

import matplotlib
import matplotlib.animation
import matplotlib.backend_bases
import matplotlib.lines
import matplotlib.ticker
import numpy as np
from PyQt5 import QtCore, QtWidgets

from .. import get_config
from ..functions import peakfit as peakfit_func
from ..functions import spectrum as spectrum_func
from ..structures.spectrum import FittedPeak
from ..workspace import UiNameGetter, UiState
from . import PeakShapeUi, component
from .manager import Manager, Thread, state_node
from .utils import savefile, showInfo


class LineAnimation:
    __slots__ = ["start_point", "end_point", "norm_line", "line", "animation"]
    callback = QtCore.pyqtSignal(tuple)

    def __init__(self) -> None:
        self.start_point: Tuple[float, float] = None
        self.end_point: Tuple[float, float] = None
        self.norm_line: matplotlib.lines.Line2D = None
        self.line: matplotlib.lines.Line2D = None
        self.animation: matplotlib.animation.FuncAnimation = None


class Widget(QtWidgets.QWidget, PeakShapeUi.Ui_Form):
    callback = QtCore.pyqtSignal(tuple)

    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.setupUi(self)

        self.animation = LineAnimation()
        self.manager.init_or_restored.connect(self.restore)
        self.manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.comboBox.addItem("Norm distribution", 1)
        self.showPushButton.clicked.connect(self.showButtonClicked)
        self.cancelPushButton.clicked.connect(self.cancel)
        self.finishPushButton.clicked.connect(self.finishPeakShape)
        self.exportPushButton.clicked.connect(self.export)

        self.plot = component.Plot(self.widget)

        self.plot.canvas.mpl_connect('button_press_event', self.mouseToggle)
        self.plot.canvas.mpl_connect('button_release_event', self.mouseToggle)
        self.plot.canvas.mpl_connect('motion_notify_event', self.mouseMove)

    def restore(self):
        self.showNormedPeaks()
        self.peak_shape.ui_state.set_state(self)

    def updateState(self):
        self.peak_shape.ui_state.fromComponents(self, [
            self.spinBox,
            self.comboBox])

    @property
    def peak_shape(self):
        return self.manager.workspace.peak_shape_tab

    @state_node
    def showButtonClicked(self):
        yield from self.showPeak()

    @state_node
    def cancel(self):
        self.peak_shape.info.peaks_manager.cancel()

        self.showNormedPeaks()

    def showPeak(self):
        info = self.peak_shape.info
        peak_num = self.spinBox.value()
        if info.spectrum is None:
            showInfo("please denoise first")
            return

        def generate_peak_manager():
            peaks = spectrum_func.splitPeaks(
                info.spectrum.mz, info.spectrum.intensity)
            peaks = [peak for peak in peaks if peak.isPeak.sum() == 1]
            peaks.sort(key=lambda peak: peak.maxIntensity, reverse=True)
            peaks = peaks[:max(1, min(peak_num, len(peaks)))]

            norm_peaks: List[FittedPeak] = []
            for peak in peaks:
                try:
                    norm_peaks.append(
                        peakfit_func.normal_distribution.getNormalizedPeak(peak))
                except:
                    pass
            manager = peakfit_func.PeaksManager(norm_peaks)
            func = peakfit_func.normal_distribution.NormalDistributionFunc.FromNormPeaks(
                norm_peaks)
            return manager, func

        info.peaks_manager, info.func = yield generate_peak_manager, "manage peaks"

        self.showNormedPeaks()

    def showNormedPeaks(self):
        ax = self.plot.ax
        ax.clear()
        if self.peak_shape.info.peaks_manager is None:
            return
        self.animation = LineAnimation()
        ax.xaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        ax.yaxis.set_tick_params(rotation=15)
        for peak in self.peak_shape.info.peaks_manager.peaks:
            ax.plot(peak.mz, peak.intensity)

        self.plotNormPeak()
        self.plot.canvas.draw()

    def plotNormPeak(self):
        info = self.peak_shape.info
        if self.animation.norm_line is not None:
            self.animation.norm_line.remove()
            del self.animation.norm_line
            self.animation.norm_line = None
        ax = self.plot.ax

        resolution = info.func.peak_fit_res
        if resolution is None:
            xlim = 2e-5
        else:
            resolution = int(resolution)
            sigma = 1 / resolution / (2 * math.sqrt(2 * math.log(2)))
            xlim = sigma * 6
        mzNorm = np.linspace(-xlim, xlim, 500)
        intensityNorm = info.func.normFunc(mzNorm)
        lines = ax.plot(mzNorm, intensityNorm, color='black', linewidth=3,
                        label="Fit, Res = " + str(resolution))
        self.animation.norm_line = lines[-1]
        ax.autoscale(True, "both", True)
        ax.legend()

    def mouseToggle(self, event: matplotlib.backend_bases.MouseEvent):
        animation = self.animation
        plot = self.plot
        ax = plot.ax
        if event.button is matplotlib.backend_bases.MouseButton.LEFT:
            if event.name == 'button_press_event':
                animation.start_point = (
                    event.xdata, event.ydata)
                animation.end_point = None
                animation.line = ax.plot([], [], color='red')[-1]
                animation.animation = matplotlib.animation.FuncAnimation(
                    plot.canvas.figure, self.mouseMovePrint, interval=1, blit=True, repeat=False, cache_frame_data=False)
            elif animation.start_point is not None and event.name == 'button_release_event':
                info = self.peak_shape.info
                if info.func is not None and animation.end_point is not None:
                    line = (animation.start_point, animation.end_point)
                    peaks = info.peaks_manager.peaks
                    indexes = [index for index, peak in enumerate(
                        peaks) if peakfit_func.linePeakCrossed(line, peak.mz, peak.intensity)]
                    if len(indexes) == len(peaks):
                        showInfo("couldn't remove all peaks")
                    elif len(indexes) > 0:
                        info.peaks_manager.rm(indexes)
                        indexes.reverse()
                        for index in indexes:
                            line = ax.lines.pop(index)
                            del line
                        info.func = peakfit_func.normal_distribution.NormalDistributionFunc.FromNormPeaks(
                            info.peaks_manager.peaks)
                        self.plotNormPeak()

                animation.animation._stop()

                del animation.animation
                animation.animation = None
                animation.line.remove()
                del animation.line
                animation.line = None
                plot.canvas.draw()

    def mouseMove(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button == matplotlib.backend_bases.MouseButton.LEFT:
            self.animation.end_point = (event.xdata, event.ydata)

    def mouseMovePrint(self, frame):
        animation = self.animation
        line = animation.line
        if line is not None:
            start = animation.start_point
            end = animation.end_point
            if start and end:
                line.set_data(((start[0], end[0]), (start[1], end[1])))
            return line,
        return ()

    @state_node
    def finishPeakShape(self):
        self.callback.emit(())

    @state_node
    def export(self):
        spectrum = self.peak_shape.info.spectrum
        ret, f = savefile("Save Peak Shape Info", "CSV file(*.csv)",
                          f"peak_shape_info {spectrum.start_time.strftime(get_config().format_export_time)}"
                          f"-{spectrum.end_time.strftime(get_config().format_export_time)}")
        if not ret:
            return

        info = self.peak_shape.info
        peaks = info.peaks_manager.peaks
        func = info.func
        with open(f, 'w', newline='') as file:
            length = len(peaks)
            height = max(len(peak.mz) for peak in peaks)

            export_peaks = -2 * np.ones((length, 2, height), dtype=float)

            for ind, peak in enumerate(peaks):
                peak_length = len(peak.mz)
                export_peaks[ind][0][:peak_length] = peak.mz
                export_peaks[ind][1][:peak_length] = peak.intensity

            writer = csv.writer(file)
            writer.writerow(
                ['Noirmal distribution',
                 'sigma:', func.peak_fit_sigma,
                 'res:', func.peak_fit_res])

            writer.writerow(['x', 'y'] * len(peaks))

            for index in self.manager.tqdm(range(export_peaks.shape[2])):
                writer.writerow(
                    [item if item > -1 else '' for item in export_peaks[:, :, index].reshape(-1)])
