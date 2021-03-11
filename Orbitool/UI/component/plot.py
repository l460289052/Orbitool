from datetime import datetime
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib import pyplot

from Orbitool.config import plot_refresh_interval


class Plot:
    def __init__(self, parentWidget: QtWidgets.QWidget):
        self.parent = parentWidget
        parentWidget.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = FigureCanvas(
            Figure(figsize=(20, 20)))
        self.toolBar = NavigationToolbar2QT(
            self.canvas, parentWidget)
        parentWidget.layout().addWidget(self.toolBar)
        parentWidget.layout().addWidget(self.canvas)
        # right class is `matplotlib.axes._subplots.AxesSubplot`, just for type hint
        self.ax: pyplot = self.canvas.figure.subplots()
        self.ax.autoscale(True)
        self.canvas.figure.tight_layout()
        # self.canvas.figure.subplots_adjust(
        #     left=0.1, right=0.999, top=0.999, bottom=0.05)

        self.canvas.mpl_connect('resize_event', self.resize_event)
        self.resized = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.resize)
        self.timer.start(plot_refresh_interval.total_seconds() * 1000)
        
    def resize_event(self, event):
        self.resized = True

    def resize(self):
        if self.resized:
            self.canvas.figure.tight_layout()
            self.canvas.draw()
            self.resized = False
           
