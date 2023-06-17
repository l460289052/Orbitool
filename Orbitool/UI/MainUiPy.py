from datetime import datetime
from pathlib import Path
import shutil
from typing import Dict, Union

from matplotlib.pyplot import get
from PyQt6 import QtCore, QtGui, QtWidgets

from ..structures.HDF5 import h5_brokens
from ..workspace import VERSION, WorkSpace, updater
from . import (CalibrationUiPy, FileUiPy, FormulaUiPy, MainUi, MassDefectUiPy,
               MassListUiPy, NoiseUiPy, PeakFitUiPy, PeakListUiPy,
               PeakShapeUiPy, SpectraListUiPy, SpectrumUiPy, TimeseriesesUiPy,
               TimeseriesUiPy)
from . import utils as UiUtils
from .manager import Manager, MultiProcess, state_node


class Window(QtWidgets.QMainWindow):

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        manager = self.manager
        self.setWindowTitle(f"Orbitool {manager.workspace.info.version}")

        dock_opt = self.DockOption

        self.setDockOptions(dock_opt.AllowNestedDocks|dock_opt.AllowTabbedDocks|dock_opt.AnimatedDocks|dock_opt.GroupedDragging|dock_opt.VerticalTabs)
        ui.settingAction.triggered.connect(self.setting_dialog)
        ui.workspaceLoadAction.triggered.connect(self.load)
        ui.workspaceSaveAction.triggered.connect(self.save)
        ui.workspaceSaveAsAction.triggered.connect(self.save_as)

        ui.configLoadAction.triggered.connect(self.loadConfig)
        ui.configSaveAction.triggered.connect(self.saveConfig)

        # tab widgets
        ui.abortPushButton.clicked.connect(self.abort_process)

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
        self.formulaDw = self.add_dock_widget(
            "Formula", self.formula)

        self.masslist = MassListUiPy.Widget(manager)
        self.massListDw = self.add_dock_widget(
            "Mass List", self.masslist, self.formulaDw)

        self.peakFitTab.show_masslist.connect(self.masslist.showMasslist)

        self.spectraList = SpectraListUiPy.Widget(manager)
        self.spectraListDw = self.add_dock_widget(
            "Spectra List", self.spectraList, self.massListDw)

        self.spectrum = SpectrumUiPy.Widget(manager)
        self.spectrumDw = self.add_dock_widget(
            "Spectrum", self.spectrum, self.spectraListDw)

        self.peakList = PeakListUiPy.Widget(manager)
        self.peakListDw = self.add_dock_widget(
            "Peak List", self.peakList, self.spectrumDw)
        self.peakFitTab.filter_selected.connect(self.peakList.filterSelected)

        self.timeseries = TimeseriesUiPy.Widget(manager)
        self.timeseriesDw = self.add_dock_widget(
            "Timeseries", self.timeseries, self.peakListDw)
        self.timeseriesesTab.click_series.connect(self.timeseries.showSeries)

        ui.tabWidget.setCurrentIndex(0)
        ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.tab_changed(0)

    def __init__(self, workspacefile=None) -> None:
        super().__init__()
        self.manager = Manager()
        self.manager.workspace = WorkSpace()

        self.ui = MainUi.Ui_MainWindow()
        self.setupUi()

        self.manager.busy_signal.connect(self.set_busy)

        self.progress_bars: Dict[int, QtWidgets.QProgressBar] = {}
        self.manager.msg.connect(self.showMsg)
        self.manager.tqdm.tqdm_signal.connect(self.showBarLabelMessage)
        self.manager.set_busy(False)
        if workspacefile is not None:
            self._load_workspace(workspacefile)
        else:
            self.manager.init_or_restored.emit()

    @property
    def workspace(self):
        return self.manager.workspace

    def set_busy(self, value):
        self.ui.menubar.setDisabled(value)
        self.ui.tabWidget.setDisabled(value)
        self.ui.processWidget.setHidden(not value)
        self.formula.setEnabled(True)

        if not value:
            for bar in self.progress_bars.values():
                bar.deleteLater()
            self.progress_bars.clear()

    def add_dock_widget(self, title, widget, after=None):
        dw = QtWidgets.QDockWidget(title)
        dw.setWidget(widget)
        dw.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        dw.setFeatures(dw.DockWidgetFeature.DockWidgetMovable | dw.DockWidgetFeature.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dw)
        if after is not None:
            self.tabifyDockWidget(after, dw)
        return dw

    def add_tab(self, widget, title):
        self.ui.tabWidget.addTab(widget, title)
        return widget

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.manager.save.emit()
        self.workspace.close()
        e.accept()

    @state_node
    def setting_dialog(self):
        from .setting import Dialog as SettingDialog
        dialog = SettingDialog()
        dialog.exec()

    @state_node
    def load(self):
        ret, f = UiUtils.openfile(
            "Load workspace", "Orbitool Workspace file(*.Orbitool)")
        if not ret:
            return
        self._load_workspace(f)

    def _load_workspace(self, f: str):
        version = updater.get_version(f)
        if updater.need_update(version):
            ret, n = UiUtils.savefile( "Update workspace and save as a new file", "Orbitool Workspace file(*.Orbitool)")
            if not ret:
                return
            shutil.copy(f, n)
            n = Path(n)
            if n.with_suffix(".orbt-tmp").exists():
                n.with_suffix(".orbt-tmp").unlink()
            n.chmod(0o666)
            updater.update(n)
            f = n
        workspace = WorkSpace(f)
        if h5_brokens:
            UiUtils.showInfo("I have try to save more data, but below data is lost\n" +
                             "\n".join(h5_brokens), "file broken, please save as a new file")
            h5_brokens.clear()
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
        if h5_brokens:
            UiUtils.showInfo("\n".join(h5_brokens), "below data was broken")
        self.manager.workspace = WorkSpace(f)

    @state_node
    def loadConfig(self):
        ret, f = UiUtils.openfile(
            "Load config from workspace file", "Orbitool Workspace file(*.Orbitool)")
        if not ret:
            return

        self.manager.workspace.load_config_from_file(f)
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
        self.ui.statusbar.showMessage(
            f"{datetime.now().replace(microsecond=0).isoformat(sep=' ')} | {msg}")

    def showBarLabelMessage(self, label: int, percent: int, msg: str):
        if (bar := self.progress_bars.get(label, None)) is None:
            bar = QtWidgets.QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(1)
            bar.setFormat("")
            self.ui.progressBarLayout.addWidget(bar)
            self.progress_bars[label] = bar
        bar.setValue(percent)
        bar.setFormat(msg)

    @state_node(mode='x')
    def file_tab_finish(self):
        self.spectraList.ui.comboBox.setCurrentIndex(-1)
        self.spectraList.ui.comboBox.setCurrentIndex(0)
        self.spectraListDw.show()
        self.spectraListDw.raise_()
        self.ui.tabWidget.setCurrentWidget(self.noiseTab)

    @state_node(mode='x', withArgs=True)
    def show_spectrum(self, spectrum):
        self.spectrum.show_spectrum(spectrum)
        self.spectrumDw.show()
        self.spectrumDw.raise_()

    @state_node(mode='x', withArgs=True)
    def noise_tab_finish(self, result):
        self.workspace.info.peak_shape_tab.spectrum = result[0]
        self.ui.tabWidget.setCurrentWidget(self.peakShapeTab)
        return self.peakShapeTab.showPeak()  # yield

    @state_node(mode='x')
    def peak_shape_tab_finish(self):
        self.ui.tabWidget.setCurrentWidget(self.calibrationTab)

    @state_node(mode='x')
    def calibration_finish(self):
        self.ui.tabWidget.setCurrentWidget(self.peakFitTab)
        self.spectraList.ui.comboBox.setCurrentIndex(1)
        self.spectraListDw.raise_()

    def abort_process(self):
        thread: MultiProcess = self.manager.running_thread
        if isinstance(thread, MultiProcess):
            thread.abort()

    def tab_changed(self, index):
        widget = self.ui.tabWidget.currentWidget()

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
