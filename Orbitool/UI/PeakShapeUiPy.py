import math
from copy import copy
from typing import Optional, Union, Tuple

import matplotlib
import matplotlib.animation
import matplotlib.backend_bases
import matplotlib.lines
import matplotlib.ticker
from PyQt5 import QtCore, QtWidgets
import numpy as np

from ..functions import peakfit as peakfit_func, spectrum as spectrum_func
from . import PeakShapeUi, component
from .manager import Manager, Thread, state_node
from ..workspace import UiNameGetter, UiState
from .utils import showInfo


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
        self.manager.inited_or_restored.connect(self.restore)
        self.manager.save.connect(self.updateState)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.comboBox.addItem("Norm distribution", 1)
        self.showPushButton.clicked.connect(self.showButtonClicked)
        self.finishPushButton.clicked.connect(self.finishPeakShape)

        self.plot = component.Plot(self.widget)

        self.plot.canvas.mpl_connect('button_press_event', self.mouseToggle)
        self.plot.canvas.mpl_connect('button_release_event', self.mouseToggle)
        self.plot.canvas.mpl_connect('motion_notify_event', self.mouseMove)

    def restore(self):
        self.showNormPeaks()
        self.peak_shape.ui_state.set_state(self)

    def updateState(self):
        self.peak_shape.ui_state.fromComponents(self, [self.spinBox])

    @property
    def peak_shape(self):
        return self.manager.workspace.peak_shape_tab

    @state_node
    def showButtonClicked(self):
        return self.showPeak()

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

            peaks = list(
                map(peakfit_func.normal_distribution.getNormalizedPeak, peaks))
            manager = peakfit_func.PeaksManager(peaks)
            func = peakfit_func.normal_distribution.NormalDistributionFunc.Factory_FromParams(
                [peak.fitted_param for peak in peaks])
            return manager, func

        info.peaks_manager, info.func = yield generate_peak_manager

        self.showNormPeaks()

    def showNormPeaks(self):
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

        # resolution = self.peak_shape.info.peaks_manager.resolution
        resolution = None
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

    def finishPeakShape(self):
        self.callback.emit(())
