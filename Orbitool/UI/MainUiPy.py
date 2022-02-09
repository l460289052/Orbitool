from typing import Union, Dict
from datetime import datetime

from PyQt5 import QtWidgets, QtCore, QtGui

from ..workspace import WorkSpace, update as workspace_update, need_update, VERSION

from .manager import Manager, state_node, MultiProcess
from . import utils as UiUtils

from . import MainUi

from . import FileUiPy, NoiseUiPy, PeakShapeUiPy, CalibrationUiPy, PeakFitUiPy, MassDefectUiPy
from . import TimeseriesesUiPy

from . import FormulaUiPy, MassListUiPy, SpectraListUiPy, PeakListUiPy, SpectrumUiPy
from . import TimeseriesUiPy


class Window(QtWidgets.QMainWindow, MainUi.Ui_MainWindow):

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)

        manager = self.manager
        self.setWindowTitle(f"Orbitool {manager.workspace.info.version}")

        self.workspaceLoadAction.triggered.connect(self.load)
        self.workspaceSaveAction.triggered.connect(self.save)
        self.workspaceSaveAsAction.triggered.connect(self.save_as)

        self.configLoadAction.triggered.connect(self.loadConfig)
        self.configSaveAction.triggered.connect(self.saveConfig)

        # tab widgets
        self.abortPushButton.clicked.connect(self.abort_process)

        self.fileTab: FileUiPy.Widget = self.add_tab(
            FileUiPy.Widget(manager), "File")
        self.fileTab.callback.connect(self.file_tab_finish)

        self.noiseTab: NoiseUiPy.Widget = self.add_tab(
            NoiseUiPy.Widget(manager), "Noise")
        self.noiseTab.selected_spectrum_average.connect(
            self.show_spectrum)
        self.noiseTab.callback.connect(self.noise_tab_finish)

        self.peakShapeTab: PeakShapeUiPy.Widget = self.add_tab(
            PeakShapeUiPy.Widget(manager), "Peak Shape")
        self.peakShapeTab.callback.connect(self.peak_shape_tab_finish)

        self.calibrationTab = self.add_tab(
            CalibrationUiPy.Widget(manager), "Calibration")
        self.calibrationTab.callback.connect(
            self.calibration_finish)

        self.peakFitTab = self.add_tab(PeakFitUiPy.Widget(manager), "Peak Fit")
        self.peakFitTab.show_spectrum.connect(self.show_spectrum)

        self.massDefectTab = self.add_tab(
            MassDefectUiPy.Widget(manager), "Mass Defect")

        self.timeseriesesTab = self.add_tab(
            TimeseriesesUiPy.Widget(manager), "Timeseries")

        # docker widgets

        self.formula = FormulaUiPy.Widget(manager)
        self.formulaDw = self.add_dockerwidget(
            "Formula", self.formula)

        self.masslist = MassListUiPy.Widget(manager)
        self.massListDw = self.add_dockerwidget(
            "Mass List", self.masslist, self.formulaDw)

        self.peakFitTab.show_masslist.connect(self.masslist.showMasslist)

        self.spectraList = SpectraListUiPy.Widget(manager)
        self.spectraListDw = self.add_dockerwidget(
            "Spectra List", self.spectraList, self.massListDw)

        self.spectrum = SpectrumUiPy.Widget(manager)
        self.spectrumDw = self.add_dockerwidget(
            "Spectrum", self.spectrum, self.spectraListDw)

        self.peakList = PeakListUiPy.Widget(manager)
        self.peakListDw = self.add_dockerwidget(
            "Peak List", self.peakList, self.spectrumDw)
        self.peakFitTab.filter_selected.connect(self.peakList.filterSelected)

        self.timeseries = TimeseriesUiPy.Widget(manager)
        self.timeseriesDw = self.add_dockerwidget(
            "Timeseries", self.timeseries, self.peakListDw)
        self.timeseriesesTab.click_series.connect(self.timeseries.showSeries)

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.tab_changed(0)

    def __init__(self, workspacefile=None) -> None:
        super().__init__()
        self.manager = Manager()
        self.manager.workspace = WorkSpace(workspacefile)

        self.setupUi(self)

        self.manager.busy_signal.connect(self.set_busy)

        self.progress_bars: Dict[int, QtWidgets.QProgressBar] = {}
        self.manager.init_or_restored.emit()
        self.manager.msg.connect(self.showMsg)
        self.manager.tqdm.tqdm_signal.connect(self.showBarLabelMessage)
        self.manager.set_busy(False)

    @property
    def workspace(self):
        return self.manager.workspace

    def set_busy(self, value):
        self.tabWidget.setDisabled(value)
        self.processWidget.setHidden(not value)
        self.formula.setEnabled(True)

        if not value:
            for bar in self.progress_bars.values():
                bar.deleteLater()
            self.progress_bars.clear()

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
        workspace = WorkSpace(f)
        if need_update(self.manager.workspace):
            UiUtils.showInfo(
                f"will update file from {workspace.info.version} to {VERSION}")
            workspace_update(workspace)
        workspace.info.version = VERSION
        self.manager.workspace = workspace
        self.manager.init_or_restored.emit()

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

    @state_node
    def loadConfig(self):
        ret, f = UiUtils.openfile(
            "Load config from workspace file", "Orbitool Workspace file(*.Orbitool)")
        if not ret:
            return

        self.manager.workspace.load_config(WorkSpace(f))
        self.manager.init_or_restored.emit()

    @state_node
    def saveConfig(self):
        ret, f = UiUtils.savefile(
            "Save config", "Orbitool Workspace file(*.Orbitool)")
        if not ret:
            return
        self.manager.save.emit()
        config = WorkSpace()
        config.load_config(self.manager.workspace)
        config.close_as(f)

    def showMsg(self, msg):
        self.statusbar.showMessage(
            f"{datetime.now().replace(microsecond=0).isoformat(sep=' ')} | {msg}")

    def showBarLabelMessage(self, label: int, percent: int, msg: str):
        if (bar := self.progress_bars.get(label, None)) is None:
            bar = QtWidgets.QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(1)
            bar.setFormat("")
            self.progressBarLayout.addWidget(bar)
            self.progress_bars[label] = bar
        bar.setValue(percent)
        bar.setFormat(msg)

    @state_node(mode='x')
    def file_tab_finish(self):
        self.spectraList.comboBox.setCurrentIndex(-1)
        self.spectraList.comboBox.setCurrentIndex(0)
        self.spectraListDw.show()
        self.spectraListDw.raise_()
        self.tabWidget.setCurrentWidget(self.noiseTab)

    @state_node(mode='x', withArgs=True)
    def show_spectrum(self, spectrum):
        self.spectrum.show_spectrum(spectrum)
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
    def calibration_finish(self):
        self.tabWidget.setCurrentWidget(self.peakFitTab)
        self.spectraList.comboBox.setCurrentIndex(1)
        self.spectraListDw.raise_()

    def abort_process(self):
        thread: MultiProcess = self.manager.running_thread
        if isinstance(thread, MultiProcess):
            thread.abort()

    def tab_changed(self, index):
        widget = self.tabWidget.currentWidget()

        def hide(dockerwidget):
            dockerwidget.hide()

        def show(dockerwodget):
            if dockerwodget.isHidden():
                dockerwodget.show()
        if widget == self.fileTab:
            list(map(hide, [self.massListDw, self.spectraListDw,
                 self.spectrumDw, self.peakListDw, self.timeseriesDw]))
        elif widget == self.noiseTab:
            list(
                map(hide, [self.massListDw, self.peakListDw, self.timeseriesDw]))
            list(map(show, [self.spectraListDw, self.spectrumDw]))
        elif widget == self.peakShapeTab:
            list(map(hide, [self.massListDw, self.spectraListDw,
                 self.spectrumDw, self.peakListDw, self.timeseriesDw]))
        elif widget == self.calibrationTab:
            list(
                map(hide, [self.massListDw, self.peakListDw, self.timeseriesDw]))
            list(map(show, [self.spectraListDw, self.spectrumDw]))
        elif widget == self.peakFitTab:
            list(map(hide, [self.timeseriesDw]))
            list(map(show, [self.massListDw, self.spectraListDw,
                            self.spectrumDw, self.peakListDw]))
        elif widget == self.massDefectTab:
            list(map(hide, [self.timeseriesDw]))
            list(map(show, [self.massListDw, self.spectraListDw,
                            self.spectrumDw, self.peakListDw]))
        elif widget == self.timeseriesesTab:
            list(map(hide, []))
            list(map(show, [self.massListDw, self.spectraListDw,
                            self.spectrumDw, self.peakListDw, self.timeseriesDw]))
