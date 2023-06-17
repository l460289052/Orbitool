from datetime import datetime
from statistics import mode
from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer

from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from ... import setting


class Plot:
    def __init__(self, parentWidget: QtWidgets.QWidget):
        self.parent = parentWidget
        parentWidget.setMinimumSize(100, 100)
        parentWidget.setLayout(QtWidgets.QVBoxLayout())
        self.canvas: FigureCanvasBase = FigureCanvas(
            Figure(figsize=(20, 20)))
        self.fig: Figure = self.canvas.figure
        self.toolBar = NavigationToolbar2QT(
            self.canvas, parentWidget)
        parentWidget.layout().addWidget(self.toolBar)
        parentWidget.layout().addWidget(self.canvas)

        self.clear()
        # self.canvas.figure.subplots_adjust(
        #     left=0.1, right=0.999, top=0.999, bottom=0.05)

        self.canvas.mpl_connect('resize_event', self.resize_event)
        self.resized = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.resize)
        self.timer.start(int(setting.plot_refresh_interval * 1000))

    def clear(self):
        self.fig.clf()
        # right class is `matplotlib.axes._subplots.AxesSubplot`, just for type hint
        self.ax: Axes = self.fig.subplots()
        self.ax.autoscale(True)
        self.fig.tight_layout()

    def resize_event(self, event):
        self.resized = True

    def resize(self):
        if self.resized:
            self.fig.tight_layout()
            self.canvas.draw()
            self.resized = False
