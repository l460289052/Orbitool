from typing import Union
from multiprocessing import Pool

from PyQt5 import QtWidgets, QtCore, QtGui

from .. import config
from ..structures import WorkSpace

from .manager import Manager, state_node
from . import utils as UiUtils

from . import MainUi

from . import FileUiPy, NoiseUiPy, PeakShapeUiPy, CalibrationUiPy, PeakFitUiPy, MassDefectUiPy
from . import TimeseriesesUiPy

from . import FormulaUiPy, MassListUiPy, SpectraListUiPy, PeakListUiPy, SpectrumUiPy
from . import CalibrationInfoUiPy, TimeseriesUiPy
from . import PeakFitFloatUiPy


class Window(QtWidgets.QMainWindow, MainUi.Ui_MainWindow):

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        manager = self.manager
        self.abortPushButton.clicked.connect(self.abort_process_pool)

        self.fileUi: FileUiPy.Widget = self.add_tab(
            FileUiPy.Widget(manager), "File")
        self.fileUi.callback.connect(self.file_tab_finish)

        self.noiseUi: NoiseUiPy.Widget = self.add_tab(
            NoiseUiPy.Widget(manager), "Noise")
        self.noiseUi.selected_spectrum_average.connect(
            self.noise_show_spectrum)
        self.noiseUi.callback.connect(self.noise_tab_finish)

        self.peakShapeUi: PeakShapeUiPy.Widget = self.add_tab(
            PeakShapeUiPy.Widget(manager), "Peak Shape")

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

        self.spectraList = SpectraListUiPy.Widget(manager)
        self.spectraListDw = self.add_dockerwidget(
            "Spectra List", self.spectraList, self.calibrationInfoDw)
        self.spectraListDw.hide()

        self.spectrum = SpectrumUiPy.Widget(manager)
        self.spectrumDw = self.add_dockerwidget(
            "Spectrum", self.spectrum, self.spectraListDw)
        self.spectrumDw.hide()

        self.peakListDw = self.add_dockerwidget(
            "Peak List", PeakListUiPy.Widget(), self.spectrumDw)
        self.peakListDw.hide()

        self.timeseries = TimeseriesUiPy.Widget()
        self.timeseriesDw = self.add_dockerwidget(
            "Timeseries", self.timeseries, self.peakListDw)
        self.tabWidget.setCurrentIndex(0)

    def __init__(self) -> None:
        super().__init__()
        self.manager = Manager()
        self.manager.workspace = WorkSpace()

        self.setupUi(self)

        self.manager.busy_signal.connect(self.set_busy)

        self.manager.pool = Pool(config.multi_cores)

        self.manager.inited.emit()
        self.manager.set_busy(False)

    def set_busy(self, value):
        self.tabWidget.setDisabled(value)
        self.processWidget.setHidden(not value)
        self.show()

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
        self.manager.workspace.close()
        e.accept()

    @state_node(mode='x', withArgs=True)
    def file_tab_finish(self, result):
        infos = result[0]
        self.spectraList.spectra_list.info.file_spectrum_info_list = infos
        self.spectraList.show_combobox_selection()
        self.spectraList.comboBox.setCurrentIndex(-1)
        self.spectraList.comboBox.setCurrentIndex(0)
        self.spectraListDw.show()
        self.spectraListDw.raise_()
        self.tabWidget.setCurrentWidget(self.noiseUi)

    @state_node(mode='x')
    def noise_show_spectrum(self):
        self.spectrum.show_spectrum(
            self.manager.workspace.noise_tab.info.current_spectrum)
        self.spectrumDw.show()
        self.spectrumDw.raise_()

    @state_node(mode='x')
    def noise_tab_finish(self):
        self.tabWidget.setCurrentIndex(self.peakShapeUi)

    def abort_process_pool(self):
        self.manager.pool.terminate()
        self.manager.pool = Pool(config.multi_cores)
