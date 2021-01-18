from typing import Union

from PyQt5 import QtWidgets, QtCore
from . import MainUi

from . import FileUiPy, NoiseUiPy, PeakShapeUiPy, CalibrationUiPy, PeakFitUiPy, MassDefectUiPy
from . import TimeseriesesUiPy

from . import FormulaUiPy, MassListUiPy, SpectraListUiPy, PeakListUiPy, SpectrumUiPy
from . import CalibrationInfoUiPy, TimeseriesUiPy
from . import PeakFitFloatUiPy


class Window(QtWidgets.QMainWindow, MainUi.Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)



    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)

        self.fileUi = self.add_tab(FileUiPy.Widget(), "File")
        self.noiseUi = NoiseUiPy.Widget()
        self.add_tab(self.noiseUi, "Noise")
        self.peakShapeUi =PeakShapeUiPy.Widget()
        self.add_tab(self.peakShapeUi, "Peak Shape")
        self.calibrationUi = self.add_tab(
            CalibrationUiPy.Widget(), "Calibration")
        self.peakFitUi = self.add_tab(PeakFitUiPy.Widget(), "Peak Fit")
        self.tabWidget.addTab(MassDefectUiPy.Widget(), "Mass Defect")
        self.timeseriesesUi = TimeseriesesUiPy.Widget()
        self.tabWidget.addTab(self.timeseriesesUi, "Timeseries")

        self.formulaDw = self.add_dockerwidget("Formula", FormulaUiPy.Widget())
        self.massListDw = self.add_dockerwidget(
            "Mass List", MassListUiPy.Widget(), self.formulaDw)
        self.calibrationInfoDw = self.add_dockerwidget(
            "Calibration Info", CalibrationInfoUiPy.Widget(), self.massListDw)
        self.spectraList = SpectraListUiPy.Widget()
        self.spectraListDw = self.add_dockerwidget(
            "Spectra List", self.spectraList, self.calibrationInfoDw)
        self.spectrumDw = self.add_dockerwidget(
            "Spectrum", SpectrumUiPy.Widget(), self.spectraListDw)
        self.spectrumDw.setHidden(True)
        self.peakListDw = self.add_dockerwidget(
            "Peak List", PeakListUiPy.Widget(), self.spectrumDw)
        self.peakListDw.setHidden(True)
        self.timeseries = TimeseriesUiPy.Widget()
        self.timeseriesDw = self.add_dockerwidget(
            "Timeseries", self.timeseries, self.peakListDw)

        self.peakfloat = PeakFitFloatUiPy.Widget()
        self.peakfloat.show()
        self.peakfloat.setWindowTitle("Peak Fit Float")

        self.noiseUi.showAveragePushButton.clicked.connect(lambda: self.spectrumDw.setHidden(False))
        self.spectraList.splitPushButton.clicked.connect(lambda:self.peakListDw.setHidden(False))

    def add_dockerwidget(self,  title, widget, after=None):
        dw = QtWidgets.QDockWidget(title)
        dw.setWidget(widget)
        dw.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dw.setFeatures(dw.DockWidgetMovable | dw.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dw)
        if after is not None:
            self.tabifyDockWidget(after, dw)
        return dw

    def add_tab(self, title, widget):
        self.tabWidget.addTab(title, widget)
        return widget
