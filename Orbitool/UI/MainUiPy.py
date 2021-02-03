from typing import Union
from multiprocessing import Pool

from PyQt5 import QtWidgets, QtCore, QtGui

from Orbitool import config
from Orbitool.structures import WorkSpace

from .manager import BaseWidget, state_node
from . import utils as UiUtils

from . import MainUi

from . import FileUiPy, NoiseUiPy, PeakShapeUiPy, CalibrationUiPy, PeakFitUiPy, MassDefectUiPy
from . import TimeseriesesUiPy

from . import FormulaUiPy, MassListUiPy, SpectraListUiPy, PeakListUiPy, SpectrumUiPy
from . import CalibrationInfoUiPy, TimeseriesUiPy
from . import PeakFitFloatUiPy



class Window(QtWidgets.QMainWindow, MainUi.Ui_MainWindow, BaseWidget):
    busy_signal = QtCore.pyqtSignal(bool)
    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)

        self.fileUi: FileUiPy.Widget = self.add_tab(
            FileUiPy.Widget(self), "File")
        self.fileUi.callback.connect(self.file_tab_finish)

        self.noiseUi: NoiseUiPy.Widget = self.add_tab(
            NoiseUiPy.Widget(self), "Noise")

        self.peakShapeUi = PeakShapeUiPy.Widget()
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
        self.calibrationInfoDw.hide()

        self.spectraList = SpectraListUiPy.Widget(self)
        self.spectraListDw = self.add_dockerwidget(
            "Spectra List", self.spectraList, self.calibrationInfoDw)
        self.spectraListDw.hide()

        self.spectrumDw = self.add_dockerwidget(
            "Spectrum", SpectrumUiPy.Widget(), self.spectraListDw)
        self.spectrumDw.hide()

        self.peakListDw = self.add_dockerwidget(
            "Peak List", PeakListUiPy.Widget(), self.spectrumDw)
        self.peakListDw.hide()

        self.timeseries = TimeseriesUiPy.Widget()
        self.timeseriesDw = self.add_dockerwidget(
            "Timeseries", self.timeseries, self.peakListDw)

    def __init__(self) -> None:
        super().__init__()
        BaseWidget.__init__(self)
        self.setupUi(self)
        
        self.tabWidget.setCurrentIndex(0)

        self.process_pool = Pool(config.multi_cores)
        self.busy = False
        self.current_workspace = WorkSpace.create_at(None)
        
    @property
    def _busy(self):
        return self.__busy

    @_busy.setter
    def _busy(self, value):
        self.tabWidget.setDisabled(value)
        self.processWidget.setHidden(not value)
        self.show()
        self.__busy = value
        self.busy_signal.emit(value)

    def add_dockerwidget(self, title, widget, after=None):
        dw = QtWidgets.QDockWidget(title)
        dw.setWidget(widget)
        dw.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dw.setFeatures(dw.DockWidgetMovable | dw.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dw)
        if after is not None:
            self.tabifyDockWidget(after, dw)
        return dw

    def add_tab(self, widget, title):
        self.tabWidget.addTab(widget, title)
        return widget

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.current_workspace.close()
        e.accept()

    @state_node(mode='x')
    def file_tab_finish(self):
        self.spectraList.show_combobox_selection()
        self.spectraList.comboBox.setCurrentIndex(0)
        self.spectraListDw.show()
        self.spectraListDw.raise_()
        self.tabWidget.setCurrentWidget(self.noiseUi)