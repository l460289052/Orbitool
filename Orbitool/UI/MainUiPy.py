from typing import Union

from PyQt5 import QtWidgets, QtCore, QtGui

from .. import config
from ..workspace import WorkSpace

from .manager import Manager, state_node, MultiProcess
from . import utils as UiUtils

from . import MainUi

from . import FileUiPy, NoiseUiPy, PeakShapeUiPy, CalibrationUiPy, PeakFitUiPy, MassDefectUiPy
from . import TimeseriesesUiPy

from . import FormulaUiPy, MassListUiPy, SpectraListUiPy, PeakListUiPy, SpectrumUiPy
from . import CalibrationInfoUiPy, TimeseriesUiPy


class Window(QtWidgets.QMainWindow, MainUi.Ui_MainWindow):

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        manager = self.manager

        self.loadAction.triggered.connect(self.load)
        self.saveAction.triggered.connect(self.save)
        self.saveAsAction.triggered.connect(self.save_as)

        # tab widgets
        self.abortPushButton.clicked.connect(self.abort_process)

        self.fileTab: FileUiPy.Widget = self.add_tab(
            FileUiPy.Widget(manager), "File")
        self.fileTab.callback.connect(self.file_tab_finish)

        self.noiseTab: NoiseUiPy.Widget = self.add_tab(
            NoiseUiPy.Widget(manager), "Noise")
        self.noiseTab.selected_spectrum_average.connect(
            self.noise_show_spectrum)
        self.noiseTab.callback.connect(self.noise_tab_finish)

        self.peakShapeTab: PeakShapeUiPy.Widget = self.add_tab(
            PeakShapeUiPy.Widget(manager), "Peak Shape")
        self.peakShapeTab.callback.connect(self.peak_shape_tab_finish)

        self.calibrationTab = self.add_tab(
            CalibrationUiPy.Widget(manager), "Calibration")
        self.calibrationTab.calcInfoFinished.connect(
            self.calibration_info_finish)
        self.calibrationTab.callback.connect(
            self.calibration_finish)

        self.peakFitTab = self.add_tab(PeakFitUiPy.Widget(manager), "Peak Fit")

        self.massDefectTab = self.add_tab(
            MassDefectUiPy.Widget(), "Mass Defect")

        self.timeseriesesTab = self.add_tab(
            TimeseriesesUiPy.Widget(), "Timeseries")

        # docker widgets

        self.formula = FormulaUiPy.Widget(manager)
        self.formulaDw = self.add_dockerwidget(
            "Formula", self.formula)

        self.massListDw = self.add_dockerwidget(
            "Mass List", MassListUiPy.Widget(), self.formulaDw)

        self.calibrationInfo = CalibrationInfoUiPy.Widget(manager)
        self.calibrationInfoDw = self.add_dockerwidget(
            "Calibration Info", self.calibrationInfo, self.massListDw)

        self.spectraList = SpectraListUiPy.Widget(manager)
        self.spectraListDw = self.add_dockerwidget(
            "Spectra List", self.spectraList, self.calibrationInfoDw)

        self.spectrum = SpectrumUiPy.Widget(manager)
        self.spectrumDw = self.add_dockerwidget(
            "Spectrum", self.spectrum, self.spectraListDw)

        self.peakListDw = self.add_dockerwidget(
            "Peak List", PeakListUiPy.Widget(manager), self.spectrumDw)

        self.timeseries = TimeseriesUiPy.Widget()
        self.timeseriesDw = self.add_dockerwidget(
            "Timeseries", self.timeseries, self.peakListDw)

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.tab_changed(0)

    def __init__(self, workspacefile=None) -> None:
        super().__init__()
        self.manager = Manager()
        self.manager.workspace = WorkSpace(workspacefile)

        self.setupUi(self)

        self.manager.busy_signal.connect(self.set_busy)

        self.manager.inited_or_restored.emit()
        self.manager.set_busy(False)

    @property
    def workspace(self):
        return self.manager.workspace

    def set_busy(self, value):
        self.tabWidget.setDisabled(value)
        self.processWidget.setHidden(not value)
        self.formula.setEnabled(True)
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
        self.workspace.close()
        e.accept()

    @state_node
    def load(self):
        ret, f = UiUtils.openfile(
            "Load workspace", "Orbitool Workspace file(*.Orbitool)")
        if not ret:
            return
        self.manager.workspace = WorkSpace(f)
        self.manager.inited_or_restored.emit()

    @state_node
    def save(self):
        self.manager.save.emit()
        self.manager.workspace.save()

    @state_node
    def save_as(self):
        ret, f = UiUtils.savefile(
            "Save workspace", "Orbitool Workspace file(*.Orbitool)")
        if not ret:
            return
        self.manager.save.emit()
        self.manager.workspace.close_as(f)
        self.manager.workspace = WorkSpace(f)

    @state_node(mode='x')
    def file_tab_finish(self):
        self.spectraList.comboBox.setCurrentIndex(-1)
        self.spectraList.comboBox.setCurrentIndex(0)
        self.spectraListDw.show()
        self.spectraListDw.raise_()
        self.tabWidget.setCurrentWidget(self.noiseTab)

    @state_node(mode='x')
    def noise_show_spectrum(self):
        self.spectrum.show_spectrum(
            self.workspace.noise_tab.info.current_spectrum)
        self.spectrumDw.show()
        self.spectrumDw.raise_()

    @state_node(mode='x', withArgs=True)
    def noise_tab_finish(self, result):
        self.workspace.peak_shape_tab.info.spectrum = result[0]
        self.tabWidget.setCurrentWidget(self.peakShapeTab)
        return self.peakShapeTab.showPeak()  # yield

    @state_node(mode='x')
    def peak_shape_tab_finish(self):
        self.tabWidget.setCurrentWidget(self.calibrationTab)

    @state_node(mode='x')
    def calibration_info_finish(self):
        self.calibrationInfo.showAllInfo()

    @state_node(mode='x')
    def calibration_finish(self):
        self.tabWidget.setCurrentWidget(self.peakFitTab)
        self.spectraList.comboBox.setCurrentIndex(1)

    def abort_process(self):
        thread: MultiProcess = self.manager.running_thread
        if issubclass(type(thread), MultiProcess):
            thread.abort()

    def tab_changed(self, index):
        widget = self.tabWidget.currentWidget()

        def hide(dockerwidget):
            dockerwidget.hide()

        def show(dockerwodget):
            if dockerwodget.isHidden():
                dockerwodget.show()
        if widget == self.fileTab:
            list(map(hide, [self.massListDw, self.calibrationInfoDw,
                            self.spectraListDw, self.spectrumDw, self.peakListDw, self.timeseriesDw]))
        elif widget == self.noiseTab:
            list(map(hide, [self.massListDw, self.calibrationInfoDw,
                            self.peakListDw, self.timeseriesDw]))
            list(map(show, [self.spectraListDw, self.spectrumDw]))
        elif widget == self.peakShapeTab:
            list(map(hide, [self.massListDw, self.calibrationInfoDw,
                            self.spectraListDw, self.spectrumDw, self.peakListDw, self.timeseriesDw]))
        elif widget == self.calibrationTab:
            list(
                map(hide, [self.massListDw, self.peakListDw, self.timeseriesDw]))
            list(map(show, [self.calibrationInfoDw,
                            self.spectraListDw, self.spectrumDw]))
        elif widget == self.peakFitTab:
            list(map(hide, [self.calibrationInfoDw, self.timeseriesDw]))
            list(map(show, [self.massListDw, self.spectraListDw,
                            self.spectrumDw, self.peakListDw]))
        elif widget == self.massDefectTab:
            list(map(hide, [self.calibrationInfoDw, self.timeseriesDw]))
            list(map(show, [self.massListDw, self.spectraListDw,
                            self.spectrumDw, self.peakListDw]))
        elif widget == self.timeseriesesTab:
            list(map(hide, [self.calibrationInfoDw]))
            list(map(show, [self.massListDw, self.spectraListDw,
                            self.spectrumDw, self.peakListDw, self.timeseriesDw]))
