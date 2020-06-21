# -*- coding: utf-8 -*-
import copy
import csv
import datetime
import math
import multiprocessing
import os
import re
import traceback
import types
from functools import wraps
from typing import List, Tuple, Union

import matplotlib.animation
import matplotlib.axes
import matplotlib.cm
import matplotlib.figure
import matplotlib.ticker
import matplotlib.patches
import numpy as np
import psutil
import pyteomics.mass
from matplotlib.backends.backend_qt5agg import (FigureCanvas,
                                                NavigationToolbar2QT)
from PyQt5 import QtCore, QtGui, QtWidgets
from sortedcontainers import SortedDict

import OrbitoolBase
import OrbitoolClass
import OrbitoolDll
import OrbitoolElement
import OrbitoolExport
import OrbitoolFormula
import OrbitoolFormulaCalc
import OrbitoolFunc
import OrbitoolOption
import OrbitoolUi

DEBUG = False


class QThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(datetime.datetime, str, int, int)

    def __init__(self, func, args: tuple):
        super(QtCore.QThread, self).__init__(None)
        self.func = func
        self.args = args

    def run(self):
        try:
            result = self.func(*self.args, self.sendStatusFunc)
            self.finished.emit((result, self.args))
        except Exception as e:
            self.finished.emit((e, self.args))

    def sendStatusFunc(self, fileTime, msg, index, length):
        self.sendStatus.emit(fileTime, msg, index, length)


def QMultiProcess(func, argsList: list, fileTime: Union[list, datetime.datetime], cpu=None) -> QThread:
    '''
    if fileTime is a list, func's first arguement must be fileTime
    '''
    return QThread(OrbitoolFunc.multiProcess, (func, argsList, fileTime, cpu))


def showInfo(content: str, cap=None):
    QtWidgets.QMessageBox.information(
        None, cap if cap is not None else 'info', str(content))


if DEBUG:
    showInfo('DEBUG')


def busy(func):
    @wraps(func)
    def decorator(self, *args, **kargs):
        if not self.setBusy(True):
            return
        try:
            func(self, *args, **kargs)
        except Exception as e:
            showInfo(str(e))
            with open('error.txt', 'a') as file:
                print('', datetime.datetime.now(), str(e), sep='\n', file=file)
                traceback.print_exc(file=file)
        self.setBusy(False)
    return decorator


def busyExcept(run):
    def busy(func):
        @wraps(func)
        def decorator(self, *args, **kargs):
            if not self.setBusy(True):
                return
            try:
                func(self, *args, **kargs)
            except Exception as e:
                showInfo(str(e))
                with open('error.txt', 'a') as file:
                    print('', datetime.datetime.now(),
                          str(e), sep='\n', file=file)
                    traceback.print_exc(file=file)
                run(self)
            self.setBusy(False)
        return decorator
    return busy


def withoutArgs(func):
    @wraps(func)
    def decorator(self, *args, **kargs):
        return func(self)
    return decorator


def threadBegin(func):
    @wraps(func)
    def decorator(self, *args, **kargs):
        if not self.setBusy(True):
            return
        try:
            thread = func(self, *args, **kargs)
            if isinstance(thread, QThread):
                self.threads.append(thread)
                thread.sendStatus.connect(self.showStatus)
                if DEBUG:
                    thread.run()
                else:
                    thread.start()
            else:
                self.setBusy(False)
        except Exception as e:
            showInfo(str(e))
            with open('error.txt', 'a') as file:
                print('', datetime.datetime.now(), str(e), sep='\n', file=file)
                traceback.print_exc(file=file)
            self.setBusy(False)
    return decorator


def threadEnd(func):
    @wraps(func)
    def decorator(self, args):
        try:
            err = args[0]
            if isinstance(err, Exception):
                raise err
            result, args = args
            func(self, result, args)
        except Exception as e:
            showInfo(str(e))
            with open('error.txt', 'a') as file:
                print('', datetime.datetime.now(),
                      str(e), sep='\n', file=file)
                traceback.print_exc(file=file)
        self.rmFinished()
        self.setBusy(False)
    return decorator


def restore(func):
    @wraps(func)
    def decorator(self, *args):
        args0, *args_ = args
        if args0 is None:
            return
        try:
            return func(self, *args)
        except Exception as e:
            showInfo(str(e))
            with open('error.txt', 'a') as file:
                print('', datetime.datetime.now(), str(e), sep='\n', file=file)
                traceback.print_exc(file=file)
    return decorator


def timer(func):
    @wraps(func)
    def decorator(self, *args):
        if self.busy:
            return
        return func(self, *args)
    return decorator


def spectraIndex(func):
    @wraps(func)
    def decorator(self, *args):
        indexes = self.spectraTableWidget.selectedIndexes()
        if len(indexes) == 0:
            raise ValueError("No spectrum was selected")
        index = indexes[0].row()
        return func(self, index)
    return decorator


def openfile(caption, filter=None, multi=False, folder=False):
    if isinstance(caption, types.FunctionType):
        raise TypeError()

    def f(func):
        if multi:
            if folder:
                raise ValueError()
            else:
                @wraps(func)
                def forfiles(self):
                    files, typ = QtWidgets.QFileDialog.getOpenFileNames(
                        caption=caption, directory='./..', filter=filter)
                    if len(files) > 0:
                        return func(self, files)
                return forfiles

        else:
            if folder:
                @wraps(func)
                def forfolder(self):
                    folder = QtWidgets.QFileDialog.getExistingDirectory(
                        caption=caption, directory='./..')
                    if len(folder) > 0 and os.path.isdir(folder):
                        return func(self, folder)
                return forfolder
            else:
                @wraps(func)
                def forfile(self):
                    file, typ = QtWidgets.QFileDialog.getOpenFileName(
                        caption=caption, directory='./..', filter=filter)
                    if len(file) > 0 and os.path.isfile(file):
                        return func(self, file)
                return forfile
    return f


def savefile(caption, filter):
    if isinstance(caption, types.FunctionType):
        raise TypeError()
    # single ext
    # ext = re.fullmatch(r'.*\(\*(\.[^.*]*)\)', filter)
    # ext = ext.group(1)

    "music(*.mp3);;image(*.jpg)"
    matches = list(re.finditer(r"[^;]*\(\*(\.[^.*]+)\)", filter))
    if not matches:
        raise ValueError(f"wrong filter {filter}")

    def f(func):
        @wraps(func)
        def decorator(self):
            path, typ = QtWidgets.QFileDialog.getSaveFileName(
                caption=caption,
                directory='./..',
                initialFilter=matches[0].group(0),
                filter=filter,
                options=QtWidgets.QFileDialog.DontConfirmOverwrite)
            if len(path) > 0:
                return func(self, path)
        return decorator
    return f


def splitterSetSize(splitter: QtWidgets.QSplitter, minSizes: List[bool]):
    '''
    sizes: List[size]
    '''
    ss = splitter.width()
    index = None
    sizes = []
    for i, mi in enumerate(minSizes):
        widget = splitter.widget(i)
        if minSizes[i]:
            sizes.append(widget.minimumSizeHint().width())
        else:
            index = i
    sizes.insert(index, ss - sum(sizes))
    splitter.setSizes(sizes)


class SpectraPlot:
    def __init__(self, parentWidget):
        self.parent = parentWidget
        parentWidget.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.toolBar = NavigationToolbar2QT(
            self.canvas, parentWidget)
        parentWidget.layout().addWidget(self.toolBar)
        parentWidget.layout().addWidget(self.canvas)
        # right class is `matplotlib.axes._subplots.AxesSubplot`, just for type hint
        self.ax: matplotlib.axes.Axes = self.canvas.figure.subplots()
        self.ax.autoscale(True)
        # self.canvas.figure.tight_layout()
        self.canvas.figure.subplots_adjust(
            left=0.1, right=0.999, top=0.999, bottom=0.05)


class Window(QtWidgets.QMainWindow, OrbitoolUi.Ui_MainWindow):
    '''
    functions'name with q means accept user's input
    '''

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        self.setupUi(self)

        # menubar
        self.workspaceImportAction.triggered.connect(self.qWorkspaceImport)
        self.workspaceExportAction.triggered.connect(self.qWorkspaceExport)

        self.optionActionImport.triggered.connect(self.qOptionImport)
        self.optionActionExport.triggered.connect(self.qOptionExport)

        # formula
        self.formulaElementAddToolButton.clicked.connect(
            self.qFormulaElementAdd)
        self.formulaIsotopeAddToolButton.clicked.connect(
            self.qFormulaIsotopeAdd)
        self.formulaIsotopeDelToolButton.clicked.connect(
            self.qFormulaIsotopeDel)
        self.formulaApplyPushButton.clicked.connect(self.qFormulaApply)
        self.formulaCalcPushButton.clicked.connect(self.qFormulaCalc)

        self.formulaElementTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        # mass list
        self.massListAddPushButton.clicked.connect(
            self.qMassListAdd)
        self.massListRemovePushButton.clicked.connect(
            self.qMassListRemoveSelected)
        self.massListMergePushButton.clicked.connect(
            self.qMassListMerge)
        self.massListImportPushButton.clicked.connect(
            self.qMassListImport)
        self.massListExportPushButton.clicked.connect(
            self.qMassListExport)

        self.massListTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        # spectra
        self.spectraTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectrumPropertyTableWidget.horizontalHeader(
        ).setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.spectraTableWidget.itemClicked.connect(self.qSpectraClicked)

        # files
        self.addFolderPushButton.clicked.connect(self.qAddFolder)
        self.addFilePushButton.clicked.connect(self.qAddFile)
        self.removeFilePushButton.clicked.connect(self.qRemoveFile)
        self.showFilePushButton.clicked.connect(self.qShowFilesSpectra)
        self.averageSelectedPushButton.clicked.connect(
            self.qAverageSelectedFile)
        self.averageAllPushButton.clicked.connect(self.qAverageAllFile)

        self.fileTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        # spectra1 & denoise
        self.spectra1ShowPushButton.clicked.connect(self.qSpectra1Show)
        self.denoiseRecalcPushButton.clicked.connect(self.qDenoiseRecalc)
        self.denoiseFinishPushButton.clicked.connect(
            lambda: self.qDenoise(True))
        self.spectra1ContinuePushButton.clicked.connect(
            lambda: self.qDenoise(False))
        self.spectrum1ExportPushButton.clicked.connect(self.qSpectrum1Export)
        self.denoiseExportPushButton.clicked.connect(
            self.qSpectrum1NoiseExport)
        self.spectrum1DenoisedExportPushButton.clicked.connect(
            self.qSpectrum1DenoisedExport)
        self.spectrum1LogScaleCheckBox.toggled.connect(
            self.qSpectrum1LogScaleToggle)
        self.spectrum1RescalePushButton.clicked.connect(self.qSpectra1Rescale)
        self.spectrum1RescaleFlag = False

        self.spectrum1TableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.spectrum1Plot = SpectraPlot(self.spectrum1Widget)
        self.spectrum1Timer = QtCore.QTimer(self)
        self.spectrum1Timer.setInterval(500)
        self.spectrum1Timer.timeout.connect(self.qSpectrum1ListFitXAxis)
        self.spectrum1Timer.start()
        self.spectrum1XAxisLeft = None

        # pre peak fit 2
        self.peakFitShowPeakPushButton.clicked.connect(
            self.qPeakFit2ShowSelectedSpectrum)
        self.peak2CancelPushButton.clicked.connect(self.qPeak2RmCancel)
        self.peak2FinishPushButton.clicked.connect(self.qPeak2Finish)
        self.peak2ExportPushButton.clicked.connect(self.qPeak2Export)

        self.peak2Widget.setLayout(QtWidgets.QVBoxLayout())
        self.peak2Canvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.peak2Widget.layout().addWidget(self.peak2Canvas)
        self.peak2Ax: matplotlib.axes.Axes = self.peak2Canvas.figure.subplots()
        self.peak2Ax.autoscale(True)
        self.peak2Canvas.mpl_connect(
            'button_press_event', self.qPeak2MouseToggle)
        self.peak2Canvas.mpl_connect(
            'button_release_event', self.qPeak2MouseToggle)
        self.peak2Canvas.mpl_connect(
            'motion_notify_event', self.qPeak2MouseMove)
        self.peak2NormLine: matplotlib.lines.Line2D = None
        self.peak2MouseStartPoint = None
        self.peak2MouseEndPoint = None
        self.peak2MouseLine: matplotlib.lines.Line2D = None
        self.peak2MouseLineAni: matplotlib.animation.FuncAnimation = None

        # calibrate
        self.calibrationAddIonToolButton.clicked.connect(
            self.qCalibrationAddIon)
        self.calibrationDelIonToolButton.clicked.connect(
            self.qCalibrationRmIon)
        self.calibratePushButton.clicked.connect(self.qInitCalibration)
        self.calibrationShowSpectrumPushButton.clicked.connect(
            self.qCalibrationShowSpectrum)
        self.calibrationShownSelectedPushButton.clicked.connect(
            self.qCalibrationShowSelected)
        self.calibrationShowAllPushButton.clicked.connect(
            self.qCalibrationShowAll)
        self.calibrationFinishPushButton.clicked.connect(
            self.qCalibrationFinish)
        self.calibrationInfoExportPushButton.clicked.connect(
            self.qCalibrationInfoExport)

        self.calibrationIonsTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.calibrationResultTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.calibrationPlot = SpectraPlot(self.calibrationWidget)

        # spectra 3 peak fit
        self.spectra3FitDefaultPushButton.clicked.connect(
            self.qSpectra3FitSpectrum)
        self.spectra3FitUseMassListPushButton.clicked.connect(
            self.qSpectrum3FitUseMassList)

        self.spectrum3PeaksMergePushButton.clicked.connect(
            self.qSpectrum3PeaksMerge)

        self.spectrum3PeaksAddPushButton.clicked.connect(
            self.qSpectrum3PeaksAdd)
        self.spectrum3PeaksAddAllPushButton.clicked.connect(
            self.qSpectrum3PeaksAddAll)

        self.spectrum3PeaksExportPushButton.clicked.connect(
            self.qSpectrum3PeaksExport)
        self.spectrum3IsotopeExportPushButton.clicked.connect(
            self.qSpectrum3IsotopeExport)

        self.spectrum3LogScaleCheckBox.toggled.connect(
            self.qSpectrum3LogScaleToggle)
        self.spectrum3RescalePushButton.clicked.connect(self.qSpectrum3Rescale)
        self.spectrum3RescaleFlag = False

        self.spectrum3PeakListTableWidget.itemDoubleClicked.connect(
            self.qSpectrum3PeakListDoubleClicked)
        self.spectrum3PeakListTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.spectrum3Plot = SpectraPlot(self.spectrum3Widget)
        self.spectrum3Timer = QtCore.QTimer(self)
        self.spectrum3Timer.setInterval(1000)
        self.spectrum3Timer.timeout.connect(self.qSpectrum3ListFitXAxis)
        self.spectrum3Timer.start()
        self.spectrum3XAxisLeft = None

        # spectrum 3 peak

        self.spectrum3PeakOriginCheckBox.toggled.connect(
            self.qSpectrum3PeakReshow)
        self.spectrum3PeakSumCheckBox.toggled.connect(
            self.qSpectrum3PeakReshow)
        self.spectrum3PeakResidualCheckBox.toggled.connect(
            self.qSpectrum3PeakReshow)
        self.spectrum3PeakLegendCheckBox.toggled.connect(
            self.qSpectrum3PeakReshow)
        self.spectrum3PeakRefitPushButton.clicked.connect(
            self.qSpectrum3PeakRefit)
        self.spectrum3PeakClosePushButton.clicked.connect(
            self.qSpectrum3PeakClose)
        self.spectrum3PeakSavePushButton.clicked.connect(
            self.qSpectrum3PeakSave)

        self.spectrum3PeakTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectrum3PeakPropertyTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.spectrum3PeakWidget.setLayout(QtWidgets.QVBoxLayout())
        self.spectrum3PeakCanvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.spectrum3PeakWidget.layout().addWidget(self.spectrum3PeakCanvas)
        self.spectrum3PeakAx: matplotlib.axes.Axes = self.spectrum3PeakCanvas.figure.subplots()
        self.spectrum3PeakAx.autoscale(True)
        self.spectrum3PeakCanvas.figure.subplots_adjust(
            left=0.2, right=0.95, top=0.95, bottom=0.2)

        self.spectrum3PeakFitGroupBox.setHidden(True)

        # spectrum 3 mass defect
        self.spectrum3MassDefectPlotPushButton.clicked.connect(
            self.qSpectrum3MassDefectPlot)
        self.spectrum3MassDefectExportPushButton.clicked.connect(
            self.qSpectrum3MassDefectExport)

        self.spectrum3MassDefectPlot = SpectraPlot(
            self.spectrum3MassDefectWidget)

        # time series
        self.timeSeriesCalcPushButton.clicked.connect(
            self.qTimeSeriesCalc)
        self.timeSeriesRemoveAllPushButton.clicked.connect(
            self.qTimeSeriesRemoveAll)
        self.timeSeriesRemoveSelectedPushButton.clicked.connect(
            self.qTimeSeriesRemoveSelected)
        self.timeSeriesesTableWidget.itemDoubleClicked.connect(
            self.qTimeSeriesDoubleClicked)
        self.timeSeriesesExportPushButton.clicked.connect(
            self.qTimeSeriesesExport)
        self.timeSeriesExportPushButton.clicked.connect(
            self.qTimeSeriesExport)
        self.timeSeriesLogScaleCheckBox.toggled.connect(
            self.qTimeSeriesLogScaleToggle)
        self.timeSeriesRescalePushButton.clicked.connect(
            self.qTimeSeriesRescale)

        self.timeSeriesesTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.timeSeriesTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.timeSeriesPlot = SpectraPlot(self.timeSeriesWidget)
        self.timeSeriesTag2Line: Dict[str, matplotlib.lines.Line2D] = {}

        # initialize splitter
        # if init too early, won't get true size
        self.show()
        splitterSetSize(self.splitter, [True, False, True])
        self.tabWidget.setCurrentWidget(self.spectra1Tab)
        splitterSetSize(self.spectra1Splitter, [True, False])
        self.tabWidget.setCurrentWidget(self.calibrationTab)
        splitterSetSize(self.calibrationSplitter, [True, True, False])
        self.tabWidget.setCurrentWidget(self.spectra3Tab)
        splitterSetSize(self.spectra3Splitter, [True, False])

        # variables initial

        self.fileList = OrbitoolClass.FileList()
        # @showFormulaOption
        self.ionCalculator: OrbitoolFormulaCalc.IonCalculatorHint = OrbitoolFormulaCalc.IonCalculator()
        self.ionCalculator.setEI('N')
        self.ionCalculator.setEI('C[13]')
        self.ionCalculator.setEI('O[18]')
        self.ionCalculator.setEI('S[34]')
        # @showCalibrationIon
        self.calibrationIonList: List[(str, OrbitoolFormula.FormulaHint)] = []

        self.workspace = OrbitoolClass.Workspace()
        self.threads = []
        self.windows = []

        self.showFormulaOption(self.ionCalculator)
        self.busy = False
        self.busyLimit = True
        self.tabWidget.setCurrentWidget(self.filesTab)

    def rmFinished(self):
        self.threads = [t for t in self.threads if not t.isFinished()]
        self.windows = [w for w in self.windows if not w.isVisible()]

    def closeEvent(self, event: QtCore.QEvent):
        current = psutil.Process()
        for child in current.children():
            child.kill()
        QtWidgets.QMainWindow.closeEvent(self, event)

    def setBusy(self, busy=True):
        if self.busy and busy:
            if not self.busyLimit:
                return True
            showInfo("wait for processing", 'busy')
            return False
        self.busy = busy
        self.splitter.setDisabled(busy)
        self.progressBar.setHidden(not busy)
        return True

    def showStatus(self, fileTime: datetime.datetime, msg: str, current: int, total: int):
        shownMsg = None
        if current >= 0:
            shownMsg = f"{self.fileList[fileTime].name if fileTime in self.fileList else ''}\
                \t\t|\t{msg}\t|\t\t{current}"
            if total > 0:
                shownMsg += '/' + str(total)
                self.progressBar.setValue(round(100 * current / total))
            else:
                self.progressBar.setValue(100)
        else:
            shownMsg = msg
        self.statusbar.showMessage(shownMsg)

    def clear(self, beginFrom=0):
        '''
        0: Files
        1: Spectra
        2: Pre peak fitting
        3: Calibration
        4: Spectra&Peak fit
        '''
        workspace = self.workspace

        def clearAndSetRow(tableWidget):
            tableWidget.clearContents()
            tableWidget.setRowCount(0)
        if beginFrom == 0:
            self.fileList.clear()
            clearAndSetRow(self.fileTableWidget)
        if beginFrom <= 1:
            workspace.spectra1Operators = None
            workspace.spectrum1 = None
            workspace.noise = None
            workspace.LOD = None
            workspace.denoisedSpectrum1 = None
            workspace.spectra2LODs = None
            workspace.denoisedSpectra2 = None
            workspace.fileTimeSpectraMaps = None

            clearAndSetRow(self.spectraTableWidget)
            clearAndSetRow(self.spectrumPropertyTableWidget)
            plot = self.spectrum1Plot
            plot.ax.clear()
            plot.canvas.draw()
        if beginFrom <= 2:
            workspace.peakFitFunc = None

            self.peak2Ax.clear()
            self.peak2Canvas.draw()
        if beginFrom <= 3:
            workspace.fileTimeCalibrations = None

            clearAndSetRow(self.calibrationResultTableWidget)
            plot = self.calibrationPlot
            plot.ax.clear()
            plot.canvas.draw()
        if beginFrom <= 4:
            workspace.calibratedSpectra3 = None
            workspace.shownSpectrum3Index = None
            workspace.spectrum3fittedPeaks = None
            workspace.spectrum3Residual = None

            clearAndSetRow(self.spectrum3PeakListTableWidget)
            plot = self.spectrum3Plot
            plot.ax.clear()
            plot.canvas.draw()
            self.spectrum3PeakFitGroupBox.setHidden(True)

            # mass defect
            plot = self.spectrum3MassDefectPlot
            plot.ax.clear()
            plot.canvas.draw()

        # time series
        self.timeSeriesTag2Line.clear()
        workspace.timeSerieses = []
        workspace.timeSeriesIndex = None

        clearAndSetRow(self.timeSeriesesTableWidget)
        clearAndSetRow(self.timeSeriesTableWidget)
        plot = self.timeSeriesPlot
        plot.ax.clear()
        plot.canvas.draw()

    def qGetOption(self):
        option = OrbitoolOption.Option()
        option.addAllWidgets(self)
        option.addObjects(self, ['calibrationIonList', 'ionCalculator'])
        option.objects['elementParas'] = OrbitoolElement.getParas()
        return option

    def qSetOption(self, option: OrbitoolOption.Option):
        self.busyLimit = False
        option.applyWidgets(self)
        self.busyLimit = True
        option.applyObjects(self)
        for key, para in option.objects['elementParas'].items():
            OrbitoolElement.setPara(key, para)
        self.showFormulaOption(self.ionCalculator)
        self.showCalibrationIon(self.calibrationIonList)

    @busy
    @withoutArgs
    @openfile(caption="Select Option file", filter="Option file(*.OrbitOption)")
    def qOptionImport(self, file):
        option = OrbitoolFunc.file2Obj(file)
        self.qSetOption(option)

    @busy
    @withoutArgs
    @savefile(caption="Save as", filter="Option file(*.OrbitOption)")
    def qOptionExport(self, file):
        option = self.qGetOption()
        OrbitoolFunc.obj2File(file, option)

    @threadBegin
    @withoutArgs
    @openfile(caption="Save as", filter="Work file(*.OrbitWork)")
    def qWorkspaceImport(self, file):
        def process(filepath, sendStatus):
            return OrbitoolFunc.file2Obj(filepath, sendStatus)

        thread = QThread(process, (file,))
        thread.finished.connect(self.workspaceImportFinished)
        return thread

    @threadEnd
    def workspaceImportFinished(self, result, args):
        self.clear(0)

        workspace: OrbitoolClass.Workspace = result['workspace']
        if not hasattr(workspace, 'version') or workspace.version < OrbitoolClass.supportedVersion:
            msg = "Not supported OrbitWork file version"
            if hasattr(workspace, 'version'):
                msg += f": {OrbitoolClass.version2Str(workspace.version)}"
            showInfo(msg)

        option: OrbitoolOption.Option = result['option']
        self.qSetOption(option)

        fileTimePaths: List[Tuple[datetime.datetime, str]
                            ] = result['fileTimePaths']
        self.workspace = workspace
        self.fileTableWidget.setRowCount(len(fileTimePaths))
        fileList = self.fileList
        for index, (time, path) in enumerate(fileTimePaths):
            if os.path.exists(path):
                fileList.addFile(path)
            while time not in fileList:
                showInfo(f"cannot find file '{path}'")
                files = QtWidgets.QFileDialog.getOpenFileNames(
                    caption=f"Select '{path}'' or more files",
                    directory='.',
                    filter="RAW files(*.RAW)")
                for path in files[0]:
                    fileList.addFile(path)
            self.showFile(time, index)

        self.showMassList(workspace.massList)

        self.showSpectra(workspace.spectra1Operators)
        self.showSpectrum1(workspace.spectrum1,
                           workspace.LOD, workspace.denoisedSpectrum1)
        self.showPeakFitFunc(workspace.peakFitFunc)
        self.showCalibrationInfoAll(workspace.fileTimeCalibrations)
        if workspace.calibratedSpectra3 is not None:
            self.showSpectrum3Peaks(
                workspace.calibratedSpectra3[workspace.shownSpectrum3Index], workspace.spectrum3fittedPeaks, workspace.spectrum3Residual)
        self.showTimeSerieses(workspace.timeSerieses)
        self.showTimeSeries(workspace.timeSeriesIndex)

    @threadBegin
    @withoutArgs
    @savefile("Save as", "Work file(*.OrbitWork)")
    def qWorkspaceExport(self, path):
        option = self.qGetOption()
        workspace = self.workspace
        fileTimePaths = []
        for (time, file) in self.fileList.timedict.items():
            fileTimePaths.append((time, file.path))

        data = {'option': option, 'workspace': workspace,
                'fileTimePaths': fileTimePaths}

        def process(path, data, sendStatus):
            return OrbitoolFunc.obj2File(path, data)

        thread = QThread(
            process, (os.path.splitext(path)[0]+'.OrbitWork', data))
        thread.finished.connect(self.workspaceExportFinished)
        return thread

    @threadEnd
    def workspaceExportFinished(self, result, args):
        pass

    @threadEnd
    def csvExportFinished(self, result, args):
        file, *_ = args
        self.showStatus(None, f"finish exporting {file}", -1, 0)

    @busy
    @withoutArgs
    def qFormulaElementAdd(self):
        key = self.formulaElementLineEdit.text().strip()
        self.formulaElementLineEdit.setText('')
        OrbitoolElement.setPara(key, [0] * 7)
        self.showFormulaOption(self.ionCalculator)

    @busy
    @withoutArgs
    def qFormulaIsotopeAdd(self):
        key = self.formulaIsotopeLineEdit.text().strip()
        self.formulaIsotopeLineEdit.setText('')
        table = self.formulaIsotopeTableWidget
        row = table.rowCount()
        table.setRowCount(row + 1)
        table.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
        table.showRow(row)

    @busy
    @withoutArgs
    def qFormulaIsotopeDel(self):
        table = self.formulaIsotopeTableWidget
        indexes = table.selectedIndexes()
        indexes = [index.row() for index in indexes]
        indexes = np.unique(indexes)
        for index in indexes[::-1]:
            table.removeRow(index)
        table.show()

    @restore
    def showFormulaOption(self, calculator: OrbitoolFormulaCalc.IonCalculatorHint = None):
        if calculator.charge == 1:
            self.formulaPositiveRadioButton.setChecked(True)
        elif calculator.charge == -1:
            self.formulaNegativeRadioButton.setChecked(False)

        self.formulaMzMinDoubleSpinBox.setValue(calculator.Mmin)
        self.formulaMzMaxDoubleSpinBox.setValue(calculator.Mmax)
        self.formulaDBEminDoubleSpinBox.setValue(calculator.DBEmin)
        self.formulaDBEmaxDoubleSpinBox.setValue(calculator.DBEmax)
        self.formulaPpmDoubleSpinBox.setValue(calculator.ppm*1e6)
        self.formulaNitrogenRuleCheckBox.setChecked(calculator.nitrogenRule)

        elements = set(calculator.getElements())
        elements.add('e')

        constElement = ['e', 'C', 'H', 'O']
        paras = list()
        getparas = OrbitoolElement.getParas()
        for ce in constElement:
            paras.append((ce, getparas[ce]))
            getparas.pop(ce)
        constElement = list(constElement)
        paras.extend(list(getparas.items()))
        table = self.formulaElementTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(paras))
        table.setVerticalHeaderLabels([key for key, _ in paras])
        for index, (key, para) in enumerate(paras):
            def setValue(column, s, editable=True):
                item = QtWidgets.QTableWidgetItem(str(s))
                if not editable:
                    item.setFlags(QtCore.Qt.NoItemFlags)
                table.setItem(
                    index, column, item)
            item = QtWidgets.QTableWidgetItem()
            if key in constElement:
                item.setFlags(QtCore.Qt.ItemIsUserCheckable)
            else:
                item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                              QtCore.Qt.ItemIsEnabled)
            item.setCheckState(
                QtCore.Qt.Checked if key in elements else QtCore.Qt.Unchecked)
            table.setItem(index, 0, item)
            if key == 'e':
                setValue(1, pyteomics.mass.nist_mass['e*'][0][0], False)
                setValue(2, para[0], False)
                setValue(3, para[1], False)
            else:
                setValue(1, pyteomics.mass.nist_mass[key][0][0], False)
                setValue(2, para[0])
                setValue(3, para[1])
            setValue(4, para[2])
            if key == 'C':
                setValue(5, '-', False)
            else:
                setValue(5, para[3])
            setValue(6, para[4])
            setValue(7, para[5])
            setValue(8, para[6])

        isotopes = calculator.getIsotopes()
        table = self.formulaIsotopeTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(isotopes))
        for index, key in enumerate(isotopes):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, key)
            setValue(1, pyteomics.mass.calculate_mass(composition={key: 1}))

    @busyExcept(lambda self: self.showFormulaOption(self.ionCalculator))
    @withoutArgs
    def qFormulaApply(self):
        eps = 1e-9
        calculator = self.ionCalculator

        def setAndReturn(attr: str, value):
            if isinstance(value, float):
                if abs(getattr(calculator, attr) - value) < eps:
                    return False
            elif getattr(calculator, attr) == value:
                return False
            setattr(calculator, attr, value)
            return True

        changed = False
        if self.formulaPositiveRadioButton.isChecked():
            changed |= setAndReturn('charge', 1)
        elif self.formulaNegativeRadioButton.isChecked():
            changed |= setAndReturn('charge', -1)

        setAndReturn('ppm', self.formulaPpmDoubleSpinBox.value() / 1e6)
        changed |= setAndReturn(
            'DBEmin', self.formulaDBEminDoubleSpinBox.value())
        changed |= setAndReturn(
            'DBEmax', self.formulaDBEmaxDoubleSpinBox.value())
        setAndReturn('Mmin', self.formulaMzMinDoubleSpinBox.value())
        setAndReturn('Mmax', self.formulaMzMaxDoubleSpinBox.value())
        changed |= setAndReturn(
            'nitrogenRule', self.formulaNitrogenRuleCheckBox.isChecked())

        table = self.formulaElementTableWidget
        elements = set(calculator.getElements())
        for index in range(table.rowCount()):
            label = table.verticalHeaderItem(index).text()
            if table.item(index, 0).checkState() == QtCore.Qt.Checked:
                if label != 'e' and label not in elements:
                    calculator.setEI(label)
            else:
                if label in elements:
                    calculator.setEI(label, False)

            def getValue(column):
                return table.item(index, column).text()
            para = [getValue(column+2) for column in range(0, 7)]
            if label == 'C':
                para[3] = 0
            para = [float(p) for p in para]
            getpara = np.array(OrbitoolElement.getPara(label), dtype=np.float)
            if np.abs(np.array(para, dtype=np.float) - getpara).max() > eps:
                changed = True
                OrbitoolElement.setPara(label, para)

        table = self.formulaIsotopeTableWidget
        isotopes = set(calculator.getIsotopes())
        for index in range(table.rowCount()):
            isotope = table.item(index, 0).text()
            if isotope in isotopes:
                isotopes.remove(isotope)
            else:
                calculator.setEI(isotope)
                changed = True
        if len(isotopes) > 0:
            changed = True
        for isotope in isotopes:
            calculator.setEI(isotope, False)
        if changed:
            calculator.clear()
        self.showFormulaOption(calculator)

    @busy
    @withoutArgs
    def qFormulaCalc(self):
        text = self.formulaInputLineEdit.text()
        try:
            mass = float(text)
            formulaList = self.ionCalculator.get(mass)
            if len(formulaList) > 0:
                self.formulaResultLineEdit.setText(
                    ', '.join([str(f) for f in formulaList]))
            else:
                self.formulaResultLineEdit.setText('None')
        except ValueError:
            formula = OrbitoolFormula.Formula(text)
            self.formulaResultLineEdit.setText(str(formula.mass()))

    def showFile(self, time: datetime.datetime, index: int):
        table = self.fileTableWidget

        def setValue(column: int, s: str):
            table.setItem(index, column, QtWidgets.QTableWidgetItem(s))

        def date2str(time: datetime.datetime):
            return time.replace(microsecond=0).isoformat()

        f: OrbitoolClass.File = self.fileList[time]
        setValue(0, f.name)
        setValue(1, date2str(f.creationDate + f.startTime))
        setValue(2, date2str(f.creationDate + f.endTime))
        setValue(3, f.path)

    def showFileTimeRange(self):
        timeRange = self.fileList.timeRange()
        if timeRange:
            self.averageStartDateTimeEdit.setDateTime(timeRange[0])
            self.averageEndDateTimeEdit.setDateTime(timeRange[1])
        else:
            now = datetime.datetime.now()
            self.averageStartDateTimeEdit.setDateTime(now)
            self.averageEndDateTimeEdit.setDateTime(now)

    @busyExcept(lambda self: self.qAddFolderExcept())
    @withoutArgs
    @openfile("Select one folder", folder=True)
    def qAddFolder(self, folder):
        table = self.fileTableWidget
        fileTimes = self.fileList.addFileFromFolder(
            folder, self.recurrenceCheckBox.isChecked(), '.raw')
        count = table.rowCount()
        table.setRowCount(count+len(fileTimes))
        for index, time in enumerate(fileTimes):
            self.showFile(time, count+index)
        self.showFileTimeRange()

    def qAddFolderExcept(self):
        table = self.fileTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(self.fileList.timedict))
        for index, fileTime in enumerate(self.fileList.timedict.keys()):
            self.showFile(fileTime, index)
        self.showFileTimeRange()

    @busy
    @withoutArgs
    @openfile("Select one or more files", "RAW files(*.RAW)", True)
    def qAddFile(self, files):
        addedFiles = []
        for path in files:
            if self.fileList.addFile(path):
                addedFiles.append(path)

        table = self.fileTableWidget
        count = table.rowCount()
        table.setRowCount(count+len(addedFiles))
        for index, path in enumerate(addedFiles):
            self.showFile(path, count+index)
        self.showFileTimeRange()

    @busy
    @withoutArgs
    def qRemoveFile(self):
        table = self.fileTableWidget
        indexes = table.selectedIndexes()
        indexes = [index.row() for index in indexes]
        indexes = np.unique(indexes)
        for index in indexes[::-1]:
            self.fileList.rmFile(table.item(index, 3).text())
            table.removeRow(index)
        table.show()
        self.showFileTimeRange()

    @busy
    @withoutArgs
    def qShowFilesSpectra(self):
        self.clear(1)
        workspace = self.workspace

        startTime = self.averageStartDateTimeEdit.dateTime().toPyDateTime()
        endTime = self.averageEndDateTimeEdit.dateTime().toPyDateTime()
        polarity = 0
        if self.averagePositiveRadioButton.isChecked():
            polarity = 1
        elif self.averageNegativeRadioButton.isChecked():
            polarity = -1

        table = self.fileTableWidget
        fileIndexes = table.selectedIndexes()
        if not fileIndexes:
            raise ValueError('No file was selected')
        fileList = self.fileList.subList(
            [table.item(index.row(), 3).text() for index in fileIndexes])

        operators = OrbitoolClass.AverageFileList(
            fileList, None, None, 1, polarity, (startTime, endTime))
        self.workspace.spectra1Operators = operators
        self.showSpectra(operators)

        self.tabWidget.setCurrentWidget(self.spectra1Tab)

    @restore
    def showSpectra(self, spectra1Operators: Union[OrbitoolClass.GetSpectrum, OrbitoolClass.GetSpectrum]):
        table = self.spectraTableWidget
        table.setRowCount(len(spectra1Operators))
        for index, operator in enumerate(spectra1Operators):
            def setValue(column: int, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))

            setValue(0, operator.shownTime[0])
            setValue(1, operator.shownTime[1])

    @threadBegin
    def qSpectraClicked(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        workspace = self.workspace
        operator = workspace.spectra1Operators[row]
        file = self.fileList[operator.fileTime]
        value = [('file', file.name)]
        table = self.spectrumPropertyTableWidget
        table.setRowCount(0)
        table.setRowCount(len(value))
        for index, (k, v) in enumerate(value):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, k)
            setValue(1, v)

    @busy
    @withoutArgs
    def qAverageSelectedFile(self):
        self.clear(1)
        workspace = self.workspace
        time = None
        N = None
        if self.averageNSpectraRadioButton.isChecked():
            N = self.averageNSpectraSpinBox.value()
        if self.averageNMinutesRadioButton.isChecked():
            time = datetime.timedelta(
                minutes=self.averageNMinutesDoubleSpinBox.value())
        startTime = self.averageStartDateTimeEdit.dateTime().toPyDateTime()
        endTime = self.averageEndDateTimeEdit.dateTime().toPyDateTime()
        ppm = self.averagePpmDoubleSpinBox.value() / 1e6
        polarity = 0
        if self.averagePositiveRadioButton.isChecked():
            polarity = 1
        elif self.averageNegativeRadioButton.isChecked():
            polarity = -1

        table = self.fileTableWidget
        fileIndexes = table.selectedIndexes()
        if not fileIndexes:
            raise ValueError('No file was selected')

        fileList = self.fileList.subList(
            [table.item(index.row(), 3).text() for index in fileIndexes])

        workspace.spectra1Operators = OrbitoolClass.AverageFileList(
            fileList, ppm, time, N, polarity, (startTime, endTime))
        self.showSpectra(workspace.spectra1Operators)
        self.tabWidget.setCurrentWidget(self.spectra1Tab)

    @busy
    @withoutArgs
    def qAverageAllFile(self):
        self.clear(1)
        workspace = self.workspace
        time = None
        N = None
        if self.averageNSpectraRadioButton.isChecked():
            N = self.averageNSpectraSpinBox.value()
        if self.averageNMinutesRadioButton.isChecked():
            time = datetime.timedelta(
                minutes=self.averageNMinutesDoubleSpinBox.value())
        startTime = self.averageStartDateTimeEdit.dateTime().toPyDateTime()
        endTime = self.averageEndDateTimeEdit.dateTime().toPyDateTime()
        ppm = self.averagePpmDoubleSpinBox.value() / 1e6
        polarity = 0
        if self.averagePositiveRadioButton.isChecked():
            polarity = 1
        elif self.averageNegativeRadioButton.isChecked():
            polarity = -1

        workspace.spectra1Operators = OrbitoolClass.AverageFileList(
            self.fileList, ppm, time, N, polarity, (startTime, endTime))

        self.showSpectra(workspace.spectra1Operators)
        self.tabWidget.setCurrentWidget(self.spectra1Tab)

    @threadBegin
    @spectraIndex
    def qSpectra1Show(self, index):
        minus = self.denoiseRemoveMinusRadioButton.isChecked()
        workspace = self.workspace
        fileList = self.fileList
        spectrum = None
        self.spectrumPropertyTableWidget.clearContents()

        operator = workspace.spectra1Operators[index]

        quantile = self.denoiseQuantileDoubleSpinBox.value()

        def process(sendStatus):
            spectrum = operator(fileList, sendStatus)
            peakAt, noise, LOD = OrbitoolFunc.getNoise(
                spectrum, quantile, sendStatus)
            denoisedSpectrum = OrbitoolFunc.denoiseWithLOD(
                spectrum, LOD, peakAt, minus, sendStatus)
            return (spectrum, LOD, denoisedSpectrum)
        thread = QThread(process, tuple())
        thread.finished.connect(self.qSpectra1ShowFinished)
        return thread

    @threadEnd
    def qSpectra1ShowFinished(self, result, args):
        spectrum, LOD, denoisedSpectrum1 = result
        workspace = self.workspace
        workspace.spectrum1 = spectrum
        workspace.LOD = LOD
        workspace.denoisedSpectrum1 = denoisedSpectrum1

        self.showSpectrum1(spectrum, LOD, denoisedSpectrum1)

    @restore
    def showSpectrum1(self, spectrum: OrbitoolBase.Spectrum, LOD: (float, float), denoisedSpectrum1: OrbitoolBase.Spectrum):
        table = self.spectrum1TableWidget

        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(spectrum.mz))

        for index in range(len(spectrum.mz)):

            def setValue(column: int, s: str):
                table.setItem(index, column, QtWidgets.QTableWidgetItem(s))

            setValue(0, "%.6f" % (spectrum.mz[index]))
            setValue(1, "%.2f" % (spectrum.intensity[index]))

        log = self.spectrum1LogScaleCheckBox.isChecked()
        plot = self.spectrum1Plot
        ax = plot.ax
        ax.clear()

        ax.set_yscale('log' if log else 'linear')

        ax.axhline(color='black', linewidth=0.5)
        ax.yaxis.set_tick_params(rotation=45)
        if not log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        ax.plot(spectrum.mz, spectrum.intensity,
                linewidth=1, color='b', label='origin')
        ax.plot(denoisedSpectrum1.mz, denoisedSpectrum1.intensity,
                linewidth=1, color='g', label='denoised')  # , linestyle='--')
        ax.axhline(LOD[0] + 3 * LOD[1], color='r', label='LOD')

        ax.legend()

        plot.canvas.draw()

    @timer
    def qSpectrum1ListFitXAxis(self):
        if self.busy or self.workspace.spectrum1 is None:
            return
        scroll = self.spectrum1AutoScrollCheckBox.isChecked()
        rescale = self.spectrum1RescaleFlag
        if not (scroll or rescale):
            return
        plot = self.spectrum1Plot
        l, r = plot.ax.get_xlim()
        scroll &= (l != self.spectrum1XAxisLeft)
        if scroll or rescale:
            workspace = self.workspace
            self.spectrum1XAxisLeft = l
            start, stop = OrbitoolFunc.indexBetween_njit(
                workspace.spectrum1.mz, (l, r))
            if scroll:
                self.spectrum1TableWidget.verticalScrollBar().setSliderPosition(start)
            if rescale:
                b = 0
                t = workspace.spectrum1.intensity[start:stop].max()

                if self.spectrum1LogScaleCheckBox.isChecked():
                    t *= 10
                    b = 1e-1
                else:
                    delta = 0.05 * t
                    b = - delta
                    t += delta
                plot.ax.set_ylim(b, t)
                self.spectrum1RescaleFlag = False
                plot.canvas.draw()

    @threadBegin
    @withoutArgs
    def qDenoiseRecalc(self):
        quantile = self.denoiseQuantileDoubleSpinBox.value()
        minus = self.denoiseRemoveMinusRadioButton.isChecked()
        workspace = self.workspace
        spectrum = workspace.spectrum1

        thread = QThread(OrbitoolFunc.denoise,
                         (spectrum, quantile, minus))
        thread.finished.connect(self.qDenoiseRecalcFinished)
        return thread

    @threadEnd
    def qDenoiseRecalcFinished(self, result, args):
        noise, LOD, denoisedSpectrum1 = result
        workspace = self.workspace
        workspace.noise = noise
        workspace.LOD = LOD
        workspace.denoisedSpectrum1 = denoisedSpectrum1
        self.showSpectrum1(workspace.spectrum1, LOD, denoisedSpectrum1)

    @busy
    @withoutArgs
    def qSpectrum1LogScaleToggle(self):
        log = self.spectrum1LogScaleCheckBox.isChecked()
        ax = self.spectrum3Plot.ax
        ax.set_yscale('log' if log else 'linear')
        if not log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        self.spectrum1RescaleFlag = True

    @busy
    @withoutArgs
    def qSpectra1Rescale(self):
        self.spectrum1RescaleFlag = True

    @threadBegin
    def qDenoise(self, withDenoising=True):
        self.clear(2)
        quantile = self.denoiseQuantileDoubleSpinBox.value()
        minus = self.denoiseRemoveMinusRadioButton.isChecked()
        fileList = self.fileList
        workspace = self.workspace
        operators = workspace.spectra1Operators

        def process(sendStatus):
            LODs = None
            spectra = []
            length = len(operators)
            maps = SortedDict()
            cpu = multiprocessing.cpu_count() - 1
            if cpu <= 0:
                cpu = 1
            with multiprocessing.Pool(cpu) as pool:
                if not withDenoising:
                    msg = "reading and averaging"
                    rets = []
                    for index, operator in enumerate(operators):
                        sendStatus(operator.fileTime, msg, index, length)
                        spectrum = operator(fileList)
                        spectra.append(spectrum)
                        maps.setdefault(spectrum.fileTime, []).append(spectrum)

                        rets.append(pool.apply_async(
                            OrbitoolFunc.getPeaks, (spectrum, )))

                    msg = "spliting peaks"
                    for index, ret in enumerate(rets):
                        sendStatus(spectra[index].fileTime, msg, index, length)
                        spectra[index].peaks = ret.get()

                else:
                    LODs = []
                    rets = []
                    msg = "reading and averaging"
                    for index, operator in enumerate(operators):
                        sendStatus(operator.fileTime, msg, index, length)
                        spectrum = operator(fileList)

                        rets.append(pool.apply_async(
                            OrbitoolFunc.denoise, (spectrum, quantile, minus)))

                    msg = "spliting and denoising"
                    for index, ret in enumerate(rets):
                        sendStatus(
                            operators[index].fileTime, msg, index, length)
                        noise, LOD, spectrum = ret.get()
                        LODs.append(LOD)
                        spectra.append(spectrum)
                        maps.setdefault(spectrum.fileTime,
                                        []).append(spectrum)
                if len(operators) > 0:
                    sendStatus(
                        operators[-1].fileTime, msg, index, length)
            return LODs, spectra, maps
        thread = QThread(process, tuple())
        thread.finished.connect(self.qDenoiseFinished)
        return thread

    @threadBegin
    @withoutArgs
    @savefile('Save as', 'csv file(*.csv)')
    def qSpectrum1NoiseExport(self, path):
        if self.workspace.noise is None:
            raise ValueError('There is no noise shown')
        thread = QThread(OrbitoolExport.exportNoise,
                         (path, self.workspace.spectrum1.fileTime, self.workspace.noise))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @threadBegin
    @withoutArgs
    @savefile('Save as', 'csv file(*.csv)')
    def qSpectrum1Export(self, path):
        if self.workspace.spectrum1 is None:
            raise ValueError('There is no spectrum shown')
        thread = QThread(OrbitoolExport.exportSpectrum,
                         (path, self.workspace.spectrum1))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @threadBegin
    @withoutArgs
    @savefile("Save as", "csv file(*.csv)")
    def qSpectrum1DenoisedExport(self, path):
        if self.workspace.denoisedSpectrum1 is None:
            raise ValueError('There is no spectrum shown')
        thread = QThread(OrbitoolExport.exportSpectrum,
                         (path, self.workspace.denoisedSpectrum1))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @threadEnd
    def qDenoiseFinished(self, result, args):
        LODs, spectra, maps = result
        workspace = self.workspace
        workspace.spectra2LODs = LODs
        workspace.denoisedSpectra2 = spectra
        workspace.fileTimeSpectraMaps = maps
        self.tabWidget.setCurrentWidget(self.peakFit2Tab)

    @busy
    @spectraIndex
    def qPeakFit2ShowSelectedSpectrum(self, index):
        workspace = self.workspace
        if workspace.denoisedSpectra2 is None:
            raise ValueError('please denoise first')
        spectrum = workspace.denoisedSpectra2[index]
        peakFitFunc = OrbitoolClass.PeakFitFunc(
            spectrum, self.peakFitNumSpinBox.value())

        self.workspace.peakFitFunc = peakFitFunc
        self.showPeakFitFunc(peakFitFunc)

        self.peak2Canvas.draw()

    def fitPeak2PlotNormPeakWithoutDraw(self):
        if self.peak2NormLine is not None:
            self.peak2NormLine.remove()
            del self.peak2NormLine
        ax = self.peak2Ax
        normMz = np.linspace(-2e-5, 2e-5, 500)
        peakFitFunc = self.workspace.peakFitFunc
        func = peakFitFunc.func
        if func is None:
            return
        normIntensity = func.normFunc(normMz)
        lines = ax.plot(normMz, normIntensity, color='black', linewidth=3,
                        label="Fit, Res = " + str(int(func.peakResFit)))
        self.peak2NormLine = lines[-1]
        ax.legend()

    @restore
    def showPeakFitFunc(self, peakFitFunc: OrbitoolClass.PeakFitFunc):
        ax = self.peak2Ax
        ax.clear()
        self.peak2MouseStartPoint = None
        self.peak2MouseEndPoint = None
        self.peak2MouseLine = None
        self.peak2MouseLineAni = None
        ax.xaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        ax.yaxis.set_tick_params(rotation=15)
        for normPeak in peakFitFunc.normPeaks:
            ax.plot(normPeak.mz, normPeak.intensity)
        self.fitPeak2PlotNormPeakWithoutDraw()

    def qPeak2MouseToggle(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button is matplotlib.backend_bases.MouseButton.LEFT and event.name == 'button_press_event':
            self.peak2MouseStartPoint = (event.xdata, event.ydata)
            self.peak2MouseEndPoint = self.peak2MouseStartPoint
            lines = self.peak2Ax.plot([], [], color='red')
            self.peak2MouseLine = lines[-1]
            self.peak2MouseLineAni = matplotlib.animation.FuncAnimation(
                self.peak2Canvas.figure, self.qPeak2PrintMouseMove, interval=20, blit=True, repeat=False)
        elif self.peak2MouseStartPoint is not None and event.name == 'button_release_event':
            workspace = self.workspace
            if workspace.peakFitFunc is not None and event.xdata is not None:
                line = (self.peak2MouseStartPoint,
                        self.peak2MouseEndPoint)
                ax = self.peak2Ax
                func = workspace.peakFitFunc
                peaks = func.normPeaks
                indexes = [index for index in range(
                    len(func.normPeaks)) if OrbitoolFunc.linePeakCrossed(line, peaks[index].mz, peaks[index].intensity)]
                if len(indexes) == len(peaks):
                    showInfo("couldn't remove all peaks")
                elif len(indexes) > 0:
                    func.rm(indexes)
                    indexes.reverse()
                    for index in indexes:
                        line = ax.lines.pop(index)
                        del line
                    self.fitPeak2PlotNormPeakWithoutDraw()

            self.peak2MouseLineAni._stop()
            del self.peak2MouseLineAni
            self.peak2MouseLineAni = None
            self.peak2MouseLine.remove()
            del self.peak2MouseLine
            self.peak2MouseLine = None
            self.peak2Canvas.draw()

    def qPeak2MouseMove(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button == matplotlib.backend_bases.MouseButton.LEFT:
            self.peak2MouseEndPoint = (event.xdata, event.ydata)

    def qPeak2PrintMouseMove(self, frame):
        line = self.peak2MouseLine
        if line is not None:
            start = self.peak2MouseStartPoint
            end = self.peak2MouseEndPoint
            if start is not None and end is not None:
                line.set_data([[start[0], end[0]], [start[1], end[1]]])
            return line,
        return ()

    @busy
    @withoutArgs
    def qPeak2RmCancel(self):
        peaks = self.workspace.peakFitFunc.cancel()
        ax = self.peak2Ax
        for peak in peaks:
            ax.plot(peak.mz, peak.intensity)
        self.fitPeak2PlotNormPeakWithoutDraw()
        self.peak2Canvas.draw()

    @busy
    @withoutArgs
    def qPeak2Finish(self):
        self.clear(3)
        if self.workspace.peakFitFunc is not None:
            self.tabWidget.setCurrentWidget(self.calibrationTab)
        else:
            showInfo('Please fit peak first')

    @busy
    @withoutArgs
    @openfile("Select one folder to save information", folder=True)
    def qPeak2Export(self, folder):
        OrbitoolExport.exportFitInfo(folder,self.workspace.peakFitFunc,self.showStatus)



    @busy
    @withoutArgs
    def qCalibrationAddIon(self):
        ions = self.calibrationLineEdit.text().split(',')
        workspace = self.workspace
        ionList = self.calibrationIonList
        index = len(ionList)
        self.calibrationIonsTableWidget.setRowCount(index+len(ions))
        for ion in ions:
            tmp = ion.strip()
            if len(tmp) == 0:
                continue
            formula = OrbitoolFormula.Formula(tmp)
            for text, f in ionList:
                if formula == f:
                    raise ValueError('There is same ion added')
            strFormulaPair = (tmp, formula)
            ionList.append(strFormulaPair)
            self.showCalibrationIonAt(index, strFormulaPair)
            index += 1
        self.calibrationIonsTableWidget.setRowCount(len(ionList))
        self.calibrationLineEdit.setText('')

    @restore
    def showCalibrationIon(self, ionList: List[Tuple[str, OrbitoolBase.FormulaHint]]):
        self.calibrationIonsTableWidget.setRowCount(len(ionList))
        for index, pair in enumerate(ionList):
            self.showCalibrationIonAt(index, pair)

    def showCalibrationIonAt(self, index, strFormulaPair: (str, OrbitoolBase.FormulaHint)):
        ion, formula = strFormulaPair
        table = self.calibrationIonsTableWidget

        def setValue(column, s):
            table.setItem(index, column, QtWidgets.QTableWidgetItem(str(s)))
        setValue(0, ion)
        setValue(1, formula.mass())

    @busy
    @withoutArgs
    def qCalibrationRmIon(self):
        indexes = self.calibrationIonsTableWidget.selectedIndexes()
        indexes = np.unique(indexes)
        table = self.calibrationIonsTableWidget
        ionList = self.calibrationIonList
        for index in indexes[::-1]:
            table.removeRow(index)
            ionList.pop(index)

    @threadBegin
    @withoutArgs
    def qInitCalibration(self):
        fileList = self.fileList
        workspace = self.workspace
        peakFitFunc = workspace.peakFitFunc
        ionList = [f for _, f in self.calibrationIonList]
        ppm = self.calibrationPpmDoubleSpinBox.value() / 1e6
        degree = self.calibrationDegreeSpinBox.value()
        useNIons = self.calibrationNIonsSpinBox.value()

        argsList = [(spectra, peakFitFunc, ionList, (degree,), ppm, useNIons)
                    for spectra in workspace.fileTimeSpectraMaps.values()]

        # DEBUG
        thread = QMultiProcess(
            OrbitoolClass.CalibrateMass, argsList, workspace.fileTimeSpectraMaps.keys())
        # thread = QMultiProcess(
        #     OrbitoolClass.CalibrateMass, argsList, workspace.fileTimeSpectraMaps.keys(), 1)

        thread.finished.connect(self.qInitCalibrationFinished)
        return thread

    @threadEnd
    def qInitCalibrationFinished(self, result, args):
        calibrations = result
        argsList = args
        calibrations: List[OrbitoolClass.CalibrateMass]
        workspace = self.workspace
        workspace.fileTimeCalibrations = SortedDict(
            [(cali.fileTime, cali) for cali in calibrations])

        self.showCalibrationInfoAll(workspace.fileTimeCalibrations)

    @restore
    def showCalibrationInfoAll(self, fileTimeCalibrations):
        fileList = self.fileList
        workspace = self.workspace
        calibrations = [
            cali for cali in fileTimeCalibrations.values()]
        x = [cali.fileTime for cali in calibrations]

        table = self.calibrationResultTableWidget
        table.clearContents()
        table.setColumnCount(len(self.calibrationIonList) + 1)
        labels = [s for s, _ in self.calibrationIonList]
        labels.append('_')
        table.setHorizontalHeaderLabels(labels)
        table.setRowCount(len(calibrations))
        table.setVerticalHeaderLabels(
            [time.strftime(r"%y%m%d %H%M") for time in x])
        data = []
        for i, cali in enumerate(calibrations):
            data.append(cali.ionsPpm)
        data = np.array(data, dtype=np.float) * 1e6

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                table.setItem(
                    i, j, QtWidgets.QTableWidgetItem(format(data[i, j], ".5f")))

        plot = self.calibrationPlot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        if data.shape[0] > 0:
            for ionIndex in range(data.shape[1]):
                ax.plot(x, data[:, ionIndex], label='ion: ' +
                        self.calibrationIonList[ionIndex][0])
        ax.xaxis.set_tick_params(rotation=45)
        ax.set_ylabel('ppm')
        ax.legend()
        ax.relim()
        ax.autoscale_view(True, True, True)
        plot.canvas.draw()

    @busy
    @spectraIndex
    def qCalibrationShowSpectrum(self, index):
        workspace = self.workspace
        if workspace.fileTimeCalibrations is None:
            raise ValueError('Please calc calibration info first')
        spectrum: OrbitoolBase.Spectrum = workspace.denoisedSpectra2[index]
        calibrator: OrbitoolClass.CalibrateMass = workspace.fileTimeCalibrations[
            spectrum.fileTime]
        spectra = workspace.fileTimeSpectraMaps[spectrum.fileTime]
        ii = OrbitoolFunc.indexNearest(spectra, spectrum.timeRange[0], method=(
            lambda spectra, index: spectra[index].timeRange[0]))
        ionsPosition = calibrator.ionsPositions[ii]
        ionsIntensity = calibrator.ionsIntensities[ii]

        plot = self.calibrationPlot
        ax = plot.ax
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        ax.plot(spectrum.mz, spectrum.intensity, color='black')

        for x, y in zip(ionsPosition, ionsIntensity):
            ax.plot([x, x], [0, y], color='red')
        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))

        ax.relim()
        ax.autoscale_view(True, True, True)
        plot.canvas.draw()

    @busy
    @withoutArgs
    def qCalibrationShowSelected(self):

        workspace = self.workspace
        table = self.calibrationResultTableWidget
        indexes = table.selectedIndexes()
        if len(indexes) == 0:
            return
        index = indexes[0].row()

        table.clear()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ['formula', 'theoretic mz', 'mz', 'ppm', 'use for calibration'])
        massCali = workspace.fileTimeCalibrations.peekitem(index)[1]
        ionList = self.calibrationIonList

        table.setRowCount(len(ionList))
        for i in range(len(ionList)):
            def setValue(column, s):
                table.setItem(i, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, ionList[i][0])
            setValue(1, massCali.ionsMz[i, 1])
            setValue(2, massCali.ionsMz[i, 0])
            setValue(3, massCali.ionsPpm[i] * 1e6)
            setValue(4, 'True' if i in massCali.minIndex else 'False')

        calc = self.ionCalculator
        r = (calc.Mmin, calc.Mmax)
        X = np.linspace(*r, 1000)
        XX = massCali.func.predictPpm(X) * 1e6
        plot = self.calibrationPlot
        ax = plot.ax
        ax.clear()

        ax.axhline(color='black', linewidth=0.5)
        ax.plot(X, XX)

        ionsMz = massCali.ionsMz
        ionsPpm = massCali.ionsPpm
        minIndex = massCali.minIndex
        maxIndex = massCali.maxIndex
        x = ionsMz[minIndex, 0]
        y = ionsPpm[minIndex]*1e6
        ax.scatter(x, y, c='black')
        x = ionsMz[maxIndex, 0]
        y = ionsPpm[maxIndex]*1e6
        ax.scatter(x, y, c='red')

        ax.set_ylabel('ppm')
        ax.set_xlim(*r)
        plot.canvas.draw()

    @threadBegin
    @withoutArgs
    @savefile("Save as", "csv file(*.csv)")
    def qCalibrationInfoExport(self, path):
        workspace = self.workspace
        if workspace.fileTimeCalibrations is None or len(workspace.fileTimeCalibrations) == 0:
            raise ValueError('There is no calibration infomation calculated')
        thread = QThread(OrbitoolExport.exportCalibrationInfo,
                         (path, self.fileList, self.calibrationIonList, workspace.fileTimeCalibrations))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @busy
    @withoutArgs
    def qCalibrationShowAll(self):
        self.showCalibrationInfoAll(self.workspace.fileTimeCalibrations)

    @threadBegin
    @withoutArgs
    def qCalibrationFinish(self):
        self.clear(4)
        workspace = self.workspace
        if workspace.fileTimeCalibrations is None or len(workspace.fileTimeCalibrations) == 0:
            raise ValueError('please calculate calibration infomation first')

        argsList = [i for i in zip(workspace.fileTimeCalibrations.values(
        ), workspace.fileTimeSpectraMaps.values())]
        fileTime = workspace.fileTimeSpectraMaps.keys()

        thread = QMultiProcess(
            OrbitoolClass.CalibrateMass.fitSpectra, argsList, fileTime)
        # thread = QMultiProcess(OrbitoolClass.CalibrateMass.fitSpectra, argsList, fileTime, 1)
        thread.finished.connect(self.qCalibrationFinished)
        return thread

    @threadEnd
    def qCalibrationFinished(self, result, args):
        calibratedSpectra3 = []
        for spectra in result:
            calibratedSpectra3.extend(spectra)
        # calibratedSpectra3.sort(key=lambda spectrum: spectrum.timeRange[0])

        workspace = self.workspace
        workspace.calibratedSpectra3 = calibratedSpectra3

        self.tabWidget.setCurrentWidget(self.spectra3Tab)

    @threadBegin
    @spectraIndex
    def qSpectra3FitSpectrum(self, index):
        workspace = self.workspace
        if workspace.calibratedSpectra3 is None:
            raise ValueError('Please calibrate first')
        workspace.shownSpectrum3Index = index
        spectrum: OrbitoolBase.Spectrum = workspace.calibratedSpectra3[index]
        peakFitFunc = workspace.peakFitFunc
        calc = self.ionCalculator
        fileTime = spectrum.fileTime

        # put calibrate into threads
        def process(sendStatus):
            fittedPeaks: List[OrbitoolBase.Peak] = peakFitFunc.fitPeaks(
                spectrum.peaks, spectrum.fileTime, sendStatus)
            msg = 'calc formula'
            length = len(fittedPeaks)
            for index, peak in enumerate(fittedPeaks):
                sendStatus(fileTime, msg, index, length)
                peak.addFormula(calc.get(peak.peakPosition))
            sendStatus(fileTime, msg, length, length)
            OrbitoolFunc.recalcFormula(fittedPeaks, calc, sendStatus)

            return fittedPeaks, OrbitoolFunc.calculateResidual(fittedPeaks, peakFitFunc.func, spectrum.fileTime, sendStatus)

        thread = QThread(process, tuple())

        thread.finished.connect(self.qSpectra3FitFinished)
        return thread

    @threadEnd
    def qSpectra3FitFinished(self, result, args):
        peaks, residual = result

        workspace = self.workspace
        workspace.spectrum3fittedPeaks = peaks
        workspace.spectrum3Residual = residual
        self.showSpectrum3Peaks(
            workspace.calibratedSpectra3[workspace.shownSpectrum3Index], peaks, residual)

    @restore
    def showSpectrum3Peaks(self, spectrum: OrbitoolBase.Spectrum, peaks: List[OrbitoolBase.Peak], residual: (np.ndarray, np.ndarray)):
        table = self.spectrum3PeakListTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(peaks))
        for index, peak in enumerate(peaks):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, format(peak.peakPosition, '.5f'))
            setValue(1, peak.formulaList)
            setValue(2, format(peak.peakIntensity, '.5e'))
            if len(peak.formulaList) == 1:
                setValue(
                    3, format((peak.peakPosition / peak.formulaList[0].mass() - 1) * 1e6, '.3f'))
            setValue(4, format(peak.area, '.5e'))
            setValue(5, peak.splitNum)
        workspace = self.workspace
        peakFitFunc = workspace.peakFitFunc
        fileTime = spectrum.fileTime

        mz = spectrum.mz
        log = self.spectrum3LogScaleCheckBox.isChecked()
        plot = self.spectrum3Plot
        ax = plot.ax
        ax.clear()
        ax.set_yscale('log' if log else 'linear')
        ax.axhline(color='black', linewidth=0.5)
        ax.yaxis.set_tick_params(rotation=45)
        if not log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        workspace = self.workspace
        ax.plot(mz, spectrum.intensity, color='black', linewidth=1)
        ax.plot(residual[0], residual[1], color='red',
                linewidth=0.5, label='residual')
        ax.legend()
        workspace = self.workspace
        mi = mz.min()
        ma = mz.max()
        ll, lr = ax.get_xlim()
        if ll > mi:
            ll = mi
        if lr < ma:
            lr = ma
        ax.set_xlim(ll, lr)

        plot.canvas.draw()
        self.spectrum3TabWidget.setCurrentWidget(self.spectrum3PlotPeakTab)
        self.spectrum3PeakFitGroupBox.setHidden(True)
        self.spectrum3MainWidget.setHidden(False)

    @timer
    def qSpectrum3ListFitXAxis(self):
        if self.busy or self.workspace.spectrum3fittedPeaks is None:
            return
        scroll = self.spectrum3AutoScrollCheckBox.isChecked()
        rescale = self.spectrum3RescaleFlag

        plot = self.spectrum3Plot
        ax = plot.ax
        l, r = ax.get_xlim()

        scroll &= (l != self.spectrum3XAxisLeft)
        if scroll or rescale:
            workspace = self.workspace
            self.spectrum3XAxisLeft = l

            peaks = workspace.spectrum3fittedPeaks
            r: range = OrbitoolFunc.indexBetween(peaks, (l, r), method=(
                lambda peaks, index: peaks[index].peakPosition))
            if scroll:
                self.spectrum3PeakListTableWidget.verticalScrollBar().setSliderPosition(r.start)

            if rescale:
                b = 0
                t = 0
                for peak in peaks[r.start:r.stop]:
                    if t < peak.peakIntensity:
                        t = peak.peakIntensity

                if self.spectrum3LogScaleCheckBox.isChecked():
                    t *= 10
                    b = 1e-1
                else:
                    delta = 0.05 * t
                    b = - delta
                    t += delta
                ax.set_ylim(b, t)
                self.spectrum3RescaleFlag = False

            yi, ya = ax.get_ylim()
            peaks = peaks[r.start:r.stop]

            def show(peak: OrbitoolBase.Peak):
                i = peak.peakIntensity
                return i > yi and i < ya
            peaks = [peak for peak in peaks if show(peak)]
            peakIntensities = np.array(
                [peak.peakIntensity for peak in peaks], dtype=np.float)

            indexes = np.flip(peakIntensities.argsort())

            annotations = [child for child in ax.get_children(
            ) if isinstance(child, matplotlib.text.Annotation)]
            for i in range(len(annotations)):
                ann = annotations.pop()
                ann.remove()
                del ann

            cnt = 0
            for index in indexes:
                peak = peaks[index]
                if len(peak.formulaList) == 0:
                    continue
                opeak = peak.originalPeak
                i = OrbitoolFunc.indexNearest_njit(
                    opeak.mz, peak.peakPosition)
                position = opeak.mz[i]
                intensity = opeak.intensity[i]
                ax.annotate(','.join([str(f) for f in peak.formulaList]),
                            xy=(position, intensity), xytext=(
                                peak.peakPosition, peak.peakIntensity),
                            arrowprops={"arrowstyle": "-", "alpha": 0.5})
                cnt += 1
                if cnt == 5:
                    break
            plot.canvas.draw()

    @busy
    def qSpectrum3PeakListDoubleClicked(self, item: QtWidgets.QTableWidgetItem):
        index = item.row()
        workspace = self.workspace
        peaks = workspace.spectrum3fittedPeaks
        peak = peaks[index]
        opeak = peak.originalPeak

        self.spectrum3PeakNumSpinBox.setValue(peak.splitNum)

        start = index
        while opeak == peaks[start].originalPeak:
            start -= 1
        start += 1
        end = start + 1
        length = len(peaks)
        while end < length and opeak == peaks[end].originalPeak:
            end += 1
        workspace.shownSpectra3PeakRange = range(start, end)
        workspace.shownSpectra3Peak = peaks[start:end]

        self.showSpectrum3Peak(workspace.shownSpectra3Peak)

    @restore
    def showSpectrum3Peak(self, shownSpectra3Peak: List[OrbitoolBase.Peak]):
        showOrigin = self.spectrum3PeakOriginCheckBox.isChecked()
        showSum = self.spectrum3PeakSumCheckBox.isChecked()
        showResidual = self.spectrum3PeakResidualCheckBox.isChecked()
        showLegend = self.spectrum3PeakLegendCheckBox.isChecked()

        workspace = self.workspace
        opeak = shownSpectra3Peak[0].originalPeak
        ax = self.spectrum3PeakAx
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        if showOrigin:
            ax.plot(opeak.mz, opeak.intensity, label='origin',
                    linewidth=2, color='black')

        sumIntensity = np.zeros_like(opeak.intensity) if showSum else None
        diffIntensity = opeak.intensity.copy() if showResidual else None

        table = self.spectrum3PeakPropertyTableWidget

        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(shownSpectra3Peak))

        peakFitFunc = workspace.peakFitFunc

        for index, peak in enumerate(shownSpectra3Peak):
            ax.plot(peak.mz, peak.intensity, label='fitted peak %d' %
                    index, linewidth=1.5)

            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))

            setValue(0, ', '.join([str(f) for f in peak.formulaList]))
            setValue(1, format(peak.peakPosition, '.5f'))
            setValue(2, format(peak.peakIntensity, '.2f'))
            if len(peak.formulaList) == 1:
                setValue(3, format((peak.peakPosition /
                                    peak.formulaList[0].mass() - 1) * 1e6, '.5f'))
                formula = peak.formulaList[0]
                if formula.isIsotope:
                    origin = formula.findOrigin()
                    peaks = workspace.spectrum3fittedPeaks
                    m = origin.mass()
                    d = m * self.ionCalculator.ppm
                    r = OrbitoolFunc.indexBetween(
                        peaks, (m - d, m + d), method=(lambda peaks, index: peaks[index].peakPosition))
                    for i in r:
                        for f in peaks[i].formulaList:
                            if f == origin:
                                setValue(4, format(peak.peakIntensity /
                                                   peaks[i].peakIntensity, '.5f'))
                                setValue(
                                    5, format(formula.relativeAbundance(), '.5f'))
                                break

            if showSum or showResidual:
                tmpItensity = peakFitFunc.func.getIntensity(opeak.mz, peak)
                if showSum:
                    sumIntensity += tmpItensity
                if showResidual:
                    diffIntensity -= tmpItensity

        if len(shownSpectra3Peak) > 1:
            if showSum:
                ax.plot(opeak.mz, sumIntensity,
                        label='fitted peak sum', linewidth=1.5)
        if showResidual:
            ax.plot(opeak.mz, diffIntensity,
                    label='peak residual', linewidth=1.5)

        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        if showLegend:
            ax.legend()
        ax.set_xlim(opeak.mz.min(), opeak.mz.max())

        table = self.spectrum3PeakTableWidget
        table.setRowCount(len(opeak.mz))
        for index in range(len(opeak.mz)):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, opeak.mz[index])
            setValue(1, opeak.intensity[index])

        self.spectrum3TabWidget.setCurrentWidget(self.spectrum3PlotPeakTab)
        self.spectrum3PeakFitGroupBox.setHidden(False)
        self.spectrum3MainWidget.setHidden(True)

    @busy
    @withoutArgs
    def qSpectrum3PeakReshow(self):
        self.showSpectrum3Peak(self.workspace.shownSpectra3Peak)

    @busy
    @withoutArgs
    def qSpectrum3PeakRefit(self):
        num = self.spectrum3PeakNumSpinBox.value()
        workspace = self.workspace
        peaks = workspace.shownSpectra3Peak
        opeak = peaks[0].originalPeak
        fittedpeaks = workspace.peakFitFunc.fitPeak(opeak, num, force=True)
        calc = self.ionCalculator
        workspace.shownSpectra3Peak = fittedpeaks
        for i, peak in enumerate(fittedpeaks):
            peak.addFormula(calc.get(peak.peakPosition))

        self.showSpectrum3Peak(fittedpeaks)

    @busy
    @withoutArgs
    def qSpectrum3PeakClose(self):
        self.spectrum3PeakFitGroupBox.setHidden(True)
        self.spectrum3MainWidget.setHidden(False)
        self.workspace.shownSpectrum3Peak = None

    @threadBegin
    @withoutArgs
    def qSpectrum3PeakSave(self):
        workspace = self.workspace
        calc = self.ionCalculator
        shownSpectrum3Peaks = workspace.spectrum3fittedPeaks
        r = workspace.shownSpectra3PeakRange
        shownSpectra3Peak = workspace.shownSpectra3Peak

        table = self.spectrum3PeakPropertyTableWidget
        for index, peak in enumerate(shownSpectra3Peak):
            strformula = table.item(index, 0).text()
            if strformula != ', '.join([str(f) for f in peak.formulaList]):
                l = []
                for s in strformula.split(','):
                    ss = s.strip()
                    if len(ss) == 0:
                        continue
                    l.append(OrbitoolFormula.Formula(ss))
                peak.formulaList = l

        for i in r:
            shownSpectrum3Peaks.pop(r.start)
        for peak in reversed(shownSpectra3Peak):
            shownSpectrum3Peaks.insert(r.start, peak)
            peak.handled = True
        spectrum = workspace.calibratedSpectra3[workspace.shownSpectrum3Index]
        residual = workspace.spectrum3Residual
        peakFitFunc = workspace.peakFitFunc

        def process(sendStatus):
            fileTime = spectrum.fileTime
            msg = "calc formula"
            sendStatus(fileTime, msg, -1, 0)
            OrbitoolFunc.recalcFormula(shownSpectrum3Peaks, calc, sendStatus)
            msg = "calc residual"
            sendStatus(fileTime, msg, -1, 0)
            opeak: OrbitoolBase.Peak = shownSpectra3Peak[0].originalPeak
            mz = residual[0]
            intensity = residual[1]
            index = OrbitoolFunc.indexNearest_njit(mz, opeak.mz[0])
            s = slice(index, index + len(opeak.mz))
            intensity[s] = opeak.intensity
            intensity = intensity[s]
            for peak in shownSpectra3Peak:
                intensity -= peakFitFunc.func._funcFit(
                    opeak.mz, *peak.fittedParam)
            return residual
        thread = QThread(process, tuple())
        thread.finished.connect(self.qSpectrum3PeakSaveFinished)
        return thread

    @threadEnd
    def qSpectrum3PeakSaveFinished(self, result, args):
        workspace = self.workspace
        workspace.spectrum3Residual = result
        self.showSpectrum3Peaks(
            workspace.calibratedSpectra3[workspace.shownSpectrum3Index], workspace.spectrum3fittedPeaks, result)
        self.workspace.shownSpectrum3Peak = None

    @threadBegin
    @spectraIndex
    def qSpectrum3FitUseMassList(self, index):
        workspace = self.workspace
        if workspace.calibratedSpectra3 is None:
            raise ValueError('Please calibrate first')
        ppm = self.massListPpmDoubleSpinBox.value()*1e-6
        workspace.shownSpectrum3Index = index
        spectrum: OrbitoolClass.CalibratedSpectrum = workspace.calibratedSpectra3[index]
        massList: OrbitoolClass.MassList = workspace.massList
        massList.ppm = ppm
        peakFitFunc = workspace.peakFitFunc
        calc = self.ionCalculator

        thread = QThread(OrbitoolClass.fitUseMassList,
                         (massList, spectrum, peakFitFunc))
        thread.finished.connect(self.qSpectra3FitFinished)
        return thread

    @threadBegin
    @withoutArgs
    def qSpectrum3PeaksMerge(self):
        workspace = self.workspace
        if workspace.spectrum3fittedPeaks is None:
            raise ValueError('Please fit first')

        def process(ionCalc, sendStatus):
            fileTime = workspace.calibratedSpectra3[workspace.shownSpectrum3Index].fileTime
            sendStatus(fileTime, 'merge peaks', -1, 0)
            newpeaks = OrbitoolFunc.mergePeaks(workspace.spectrum3fittedPeaks, self.spectrum3PeaksMergePpmDoubleSpinBox.value(
            ) * 1e-6, workspace.peakFitFunc.func, self.ionCalculator)
            sendStatus(fileTime, 'calc residual', -1, 0)
            return newpeaks, OrbitoolFunc.calculateResidual(newpeaks, workspace.peakFitFunc.func, fileTime, sendStatus)
        thread = QThread(process, (self.ionCalculator,))
        thread.finished.connect(self.qSpectra3FitFinished)
        return thread

    @busy
    @withoutArgs
    def qSpectrum3PeaksAdd(self):
        indexes = self.spectrum3PeakListTableWidget.selectedIndexes()
        indexes=np.unique([index.row() for index in indexes])
        workspace = self.workspace
        massList = workspace.massList
        peaks = workspace.spectrum3fittedPeaks
        toBeAdded: List[OrbitoolBase.Peak] = [
            peaks[index] for index in indexes]
        massList.addPeaks(toBeAdded)
        self.showMassList(massList)

    @busy
    @withoutArgs
    def qSpectrum3PeaksAddAll(self):
        workspace = self.workspace
        massList = workspace.massList
        massList.addPeaks(workspace.spectrum3fittedPeaks)
        self.showMassList(massList)

    @threadBegin
    @withoutArgs
    @savefile("save as", "csv file(*.csv)")
    def qSpectrum3PeaksExport(self, path):
        workspace = self.workspace
        if workspace.shownSpectrum3Index is None:
            raise ValueError('There is no spectrum shown')
        thread = QThread(OrbitoolExport.exportPeakList, (path,
                                                          workspace.calibratedSpectra3[workspace.shownSpectrum3Index].fileTime, workspace.spectrum3fittedPeaks))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @threadBegin
    @withoutArgs
    @savefile("save as", "csv file(*.csv)")
    def qSpectrum3IsotopeExport(self, path):
        workspace = self.workspace
        if workspace.shownSpectrum3Index is None:
            raise ValueError('There is no spectrum shown')
        thread = QThread(OrbitoolExport.exportIsotope, (path,
                                                         workspace.calibratedSpectra3[workspace.shownSpectrum3Index].fileTime, workspace.spectrum3fittedPeaks))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @threadBegin
    @withoutArgs
    def qSpectrum3LogScaleToggle(self):
        log = self.spectrum3LogScaleCheckBox.isChecked()
        ax = self.spectrum3Plot.ax
        ax.set_yscale('log' if log else 'linear')
        if not log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        self.spectrum3RescaleFlag = True

    @threadBegin
    @withoutArgs
    def qSpectrum3Rescale(self):
        self.spectrum3RescaleFlag = True

    def spectrum3MassDefect(self) -> (tuple, tuple):
        DBE = self.spectrum3MassDefectDBERadioButton.isChecked()
        gry = self.spectrum3MassDefectShowGreyCheckBox.isChecked()

        peaks = self.workspace.spectrum3fittedPeaks
        if peaks is None:
            raise ValueError('please fit spectrum first')
        clr_peaks = [peak for peak in peaks if len(peak.formulaList) > 0]
        clr_formula = [peak.formulaList[0] if len(peak.formulaList) == 1 else None for peak in clr_peaks]
        for index in range(len(clr_formula)):
            if clr_formula[index] is None:
                peak=clr_peaks[index]
                def ppm(formula: OrbitoolFormula.FormulaHint):
                    return peak.peakPosition/formula.mass()-1
                closestformula=peak.formulaList[0]
                for formula in peak.formulaList[1:]:
                    if abs(ppm(formula)) < abs(ppm(closestformula)):
                        closestformula = formula
                clr_formula[index]=closestformula
        if DBE:
            clr_color = [formula.DBE() for formula in clr_formula]
            clr_color = np.array(clr_color, dtype=np.float)
        else:
            element = self.spectrum3MassDefectElementLineEdit.text()
            clr_color = [formula[element] for formula in clr_formula]
            clr_color = np.array(clr_color, dtype=np.int)

        clr_x = [peak.peakPosition for peak in clr_peaks]
        clr_x = np.array(clr_x, dtype=np.float)
        clr_y = clr_x - np.round(clr_x)
        clr_size = np.array(
            [peak.peakIntensity for peak in clr_peaks], dtype=np.float)

        if gry:
            gry_peaks = [peak for peak in peaks if len(peak.formulaList) != 1]
            gry_x = [peak.peakPosition for peak in gry_peaks]
            gry_x = np.array(gry_x, dtype=np.float)
            gry_y = gry_x - np.round(gry_x)
            gry_size = np.array(
                [peak.peakIntensity for peak in gry_peaks], dtype=np.float)
        else:
            gry_x = np.zeros(0, dtype=np.float)
            gry_y = gry_x
            gry_size = gry_x
            
        return ((clr_x, clr_y, clr_size, clr_color), (gry_x, gry_y, gry_size))


    @busy
    @withoutArgs
    def qSpectrum3MassDefectPlot(self):
        cmap = matplotlib.cm.rainbow
        plot = self.spectrum3MassDefectPlot
        fig: matplotlib.figure.Figure = plot.canvas.figure
        fig.clf()
        plot.ax = fig.subplots()
        ax = plot.ax
        miFactor = math.exp(
            self.spectrum3MassDefectMiSizeHorizontalSlider.value() / 20.0)
        maFactor = math.exp(
            self.spectrum3MassDefectMaSizeHorizontalSlider.value() / 20.0)

        DBE = self.spectrum3MassDefectDBERadioButton.isChecked()
        log = self.spectrum3MassDefectIntensityLogCheckBox.isChecked()

        ((clr_x, clr_y, clr_size, clr_color),
         (gry_x, gry_y, gry_size)) = self.spectrum3MassDefect()

        if log:
            clr_size = np.log(clr_size + 1) - 1
            gry_size = np.log(gry_size + 1) - 1

        if len(gry_x) > 0:
            maximum = np.max((clr_size.max(), gry_size.max()))
        else:
            maximum = clr_size.max()
        
        if log:
            maximum /= 70
        else:
            maximum /= 200
        maximum /= maFactor
        minimum = 5*miFactor

        ax.clear()
        gry_size /= maximum
        gry_size[gry_size < minimum] = minimum
        ax.scatter(gry_x, gry_y, s=gry_size, c='grey',
                    linewidths=0.5, edgecolors='k')

        clr_size /= maximum
        clr_size[clr_size < minimum] = minimum
        sc = ax.scatter(clr_x, clr_y, s=clr_size, c=clr_color,
                        cmap=cmap, linewidths=0.5, edgecolors='k')
        clrb = fig.colorbar(sc)
        element = self.spectrum3MassDefectElementLineEdit.text()
        clrb.set_label('DBE' if DBE else f'Element {element}', rotation=270)

        ax.autoscale(True)
        fig.tight_layout()

        plot.canvas.draw()

    @busy
    @withoutArgs
    @savefile(caption="Save as", filter="csv file(*.csv)")
    def qSpectrum3MassDefectExport(self, path):
        OrbitoolExport.exportMassDefect(path,*self.spectrum3MassDefect(), self.showStatus)

    @busy
    @withoutArgs
    def qMassListAdd(self):
        masses = self.massListLineEdit.text().split(',')
        masses = [mass.strip() for mass in masses]
        masses = [mass for mass in masses if len(mass) > 0]
        massList = self.workspace.massList
        peaks = []
        for mass in masses:
            peakPosition = None
            formulaList = []
            try:
                peakPosition = float(mass)
            except ValueError:
                formula = OrbitoolFormula.Formula(mass)
                formulaList.append(formula)
                peakPosition = formula.mass()
            peaks.append(OrbitoolBase.MassListPeak(
                peakPosition, formulaList, 1, True))
        massList.addPeaks(peaks)
        self.showMassList(massList)

    @restore
    def showMassList(self, massList: OrbitoolBase.MassList):
        workspace = self.workspace
        table = self.massListTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(massList))
        for index, speak in enumerate(massList):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, speak.peakPosition)
            setValue(1, ', '.join([str(f) for f in speak.formulaList]))
            setValue(2, speak.splitNum)

    @busy
    @withoutArgs
    def qMassListRemoveSelected(self):
        table = self.massListTableWidget
        indexes = table.selectedIndexes()
        indexes = np.unique([index.row() for index in indexes])
        massList = self.workspace.massList
        massList.popPeaks(indexes)
        # indexes.sort(reverse=True)
        # massList = self.workspace.massList
        # for index in indexes:
        #     massList.popPeaks(index)
        #     # table.removeRow(index) # error...
        self.showMassList(massList)

    @busy
    @withoutArgs
    @openfile("Select Mass list", "Mass list file(*.OrbitMassList);;csv file(*.csv)")
    def qMassListMerge(self, file):
        workspace = self.workspace
        ext = os.path.splitext(file)[1].lower()
        if ext == '.OrbitMassList'.lower():
            massList: OrbitoolBase.MassList = OrbitoolFunc.file2Obj(file)
            if not isinstance(massList, OrbitoolBase.MassList):
                raise ValueError('wrong file')
        elif ext == '.csv':
            with open(file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                peaks = []
                for index, row in enumerate(reader):
                    peakPosition = None
                    formulaList = []
                    if len(row) == 0:
                        continue
                    mass = row[0].strip()
                    if len(mass) == 0 and len(row) > 1:
                        mass = row[1].strip()
                    try:
                        peakPosition = float(mass)
                    except ValueError:
                        formula = OrbitoolFormula.Formula(mass)
                        formulaList.append(formula)
                        peakPosition = formula.mass()
                    peaks.append(OrbitoolBase.MassListPeak(
                        peakPosition, formulaList, 1, True))
                massList = OrbitoolBase.MassList()
                massList.addPeaks(peaks)
        workspace.massList.addPeaks(massList)
        self.showMassList(workspace.massList)

    @busy
    @withoutArgs
    @openfile("Select Mass list", "Mass list file(*.OrbitMassList);;csv file(*.csv)")
    def qMassListImport(self, file):
        workspace = self.workspace
        ext = os.path.splitext(file)[1].lower()
        massList = None
        if ext == '.OrbitMassList'.lower():
            massList: OrbitoolBase.MassList = OrbitoolFunc.file2Obj(file)
            if not isinstance(massList, OrbitoolBase.MassList):
                raise ValueError('wrong file')
        elif ext == '.csv':
            with open(file) as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                peaks = []
                for index, row in enumerate(reader):
                    peakPosition = None
                    formulaList = []
                    if len(row) == 0:
                        continue
                    mass = row[0].strip()
                    if len(mass) == 0 and len(row) > 1:
                        mass = row[1].strip()
                    try:
                        peakPosition = float(mass)
                    except ValueError:
                        formula = OrbitoolFormula.Formula(mass)
                        formulaList.append(formula)
                        peakPosition = formula.mass()
                    peaks.append(OrbitoolBase.MassListPeak(
                        peakPosition, formulaList, 1, True))
                massList = OrbitoolBase.MassList()
                massList.addPeaks(peaks)
        workspace.massList = massList
        self.showMassList(massList)

    @busy
    @withoutArgs
    @savefile("Save as", "Mass list file(*.OrbitMassList);;csv file(*.csv)")
    def qMassListExport(self, path):
        ext = os.path.splitext(path)[1].lower()
        massList = self.workspace.massList
        if ext == '.OrbitMassList'.lower():
            OrbitoolFunc.obj2File(path, massList)
        elif ext == '.csv':
            OrbitoolExport.exportMassList(path, massList)

    @threadBegin
    @withoutArgs
    def qTimeSeriesCalc(self):
        workspace = self.workspace
        if workspace.calibratedSpectra3 is None:
            raise ValueError('please calibrate mass first')
        mz = []
        ppm = self.timeSeriesPpmDoubleSpinBox.value() / 1e6
        tag = []
        if self.timeSeriesMzRadioButton.isChecked():
            tmp = self.timeSeriesMzDoubleSpinBox.value()
            mz.append(tmp)
            tag.append("%.4f with ppm=%.2f" % (tmp, ppm*1e6))
        elif self.timeSeriesFormulaRadioButton.isChecked():
            tmp = self.timeSeriesFormulaLineEdit.text().strip()
            formula = OrbitoolFormula.Formula(tmp)
            mz.append(formula.mass())
            tag.append("%s with ppm=%.2f" % (tmp, ppm*1e6))
        elif self.timeSeriesMzRangeRadioButton.isChecked():
            l = self.timeSeriesMzRangeLDoubleSpinBox.value()
            r = self.timeSeriesMzRangeRDoubleSpinBox.value()
            mz.append((l + r) / 2)
            ppm = r / mz - 1
            tag.append('%.4f-%.4f' % (l, r))
        else:
            speaks = None
            if self.timeSeriesSelectedPeaksRadioButton.isChecked():
                indexes = self.spectrum3PeakListTableWidget.selectedIndexes()
                indexes=np.unique([index.row() for index in indexes])
                peaks = workspace.spectrum3fittedPeaks
                speaks = [peaks[index] for index in indexes]
            elif self.timeSeriesSelectedMassListRadioButton.isChecked():
                indexes = self.massListTableWidget.selectedIndexes()
                indexes=np.unique([index.row() for index in indexes])
                massList = workspace.massList
                speaks = [massList[index] for index in indexes]
            elif self.timeSeriesMassListRadioButton.isChecked():
                speaks = workspace.massList
            else:
                raise ValueError('Please select a method')
            toBeAddedMz = [speak.peakPosition for speak in speaks]

            def toTag(speak: OrbitoolBase.Peak):
                if len(speak.formulaList) > 0:
                    return ','.join([str(f) for f in speak.formulaList]) + ' with ppm=%.2f' % (ppm*1e6)
                return "%.4f with ppm=%.2f" % (speak.peakPosition, ppm*1e6)
            toBeAddedTag = [toTag(speak) for speak in speaks]
            mz.extend(toBeAddedMz)
            tag.extend(toBeAddedTag)
        tag2Line = self.timeSeriesTag2Line
        for index in reversed(range(len(mz))):
            if tag[index] in tag2Line:
                mz.pop(index)
                tag.pop(index)
        spectra = workspace.calibratedSpectra3
        peakFitFUnc = workspace.peakFitFunc

        def process(mz, tag, sendStatus):
            length = len(mz)
            timeSerieses = []
            now = datetime.datetime.now()
            for index, (m, t) in enumerate(zip(mz, tag)):
                sendStatus(now, t, index, length)
                timeSerieses.append(OrbitoolClass.getTimeSeries(
                    m, ppm, spectra, peakFitFUnc, t, sendStatus))
            return timeSerieses
        thread = QThread(process, (mz, tag))
        thread.finished.connect(self.qTimeSeriesCalcFinished)
        return thread

    @threadEnd
    def qTimeSeriesCalcFinished(self, result, args):
        timeSerieses = self.workspace.timeSerieses
        s = set(timeSerieses)
        for timeSeries in result:
            if timeSeries not in s:
                timeSerieses.append(timeSeries)
        self.showTimeSerieses(timeSerieses)

    @restore
    def showTimeSerieses(self, timeSerieses: List[OrbitoolBase.TimeSeries]):
        maps = self.timeSeriesTag2Line
        length = len(timeSerieses)
        timeSerieses: List[OrbitoolBase.TimeSeries] = [
            timeSeries for timeSeries in timeSerieses if timeSeries.tag not in maps]
        start = length-len(timeSerieses)
        table = self.timeSeriesesTableWidget
        table.setRowCount(length)
        for index, timeSeries in enumerate(timeSerieses):
            row = start+index

            def setValue(column, s):
                table.setItem(row, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, timeSeries.tag)
            setValue(1, timeSeries.mz)
            setValue(2, timeSeries.ppm * 1e6)

        spectra = self.workspace.calibratedSpectra3
        length = 0 if spectra is None else len(spectra)
        ax = self.timeSeriesPlot.ax
        msg = [
            "please check mz or ppm of time series below, I may have no enough infomation about it"]
        for timeSeries in timeSerieses:
            if len(timeSeries.time) < length / 3:
                msg.append(timeSeries.tag)
                if len(timeSeries.time) == 0:
                    continue
            lines = ax.plot(timeSeries.time,
                            timeSeries.intensity, label=timeSeries.tag)
            maps[timeSeries.tag] = lines[-1]
        if len(msg) > 1:
            showInfo('\n'.join(msg))
        ax.xaxis.set_tick_params(rotation=30)
        ax.legend()
        self.timeSeriesRescale()

    @busy
    @withoutArgs
    def qTimeSeriesRemoveAll(self):
        self.workspace.timeSerieses.clear()
        self.timeSeriesesTableWidget.clearContents()
        self.timeSeriesesTableWidget.setRowCount(0)
        for line in self.timeSeriesTag2Line.values():
            line.remove()
            del line
        self.timeSeriesTag2Line.clear()
        self.timeSeriesPlot.ax.legend()
        self.timeSeriesPlot.canvas.draw()
        self.timeSeriesTableWidget.clearContents()
        self.timeSeriesTableWidget.setRowCount(0)
        self.workspace.timeSeriesIndex = None

    @busy
    @withoutArgs
    def qTimeSeriesRemoveSelected(self):
        indexes = self.timeSeriesesTableWidget.selectedIndexes()
        indexes = np.unique([index.row() for index in indexes])
        workspace = self.workspace
        timeSeries = workspace.timeSerieses
        tag2Line = self.timeSeriesTag2Line
        table = self.timeSeriesesTableWidget
        for index in reversed(indexes):
            table.removeRow(index)
            deleted = timeSeries.pop(index)
            if deleted.tag in tag2Line:
                line = tag2Line.pop(deleted.tag)
                line.remove()
                del line
        plot = self.timeSeriesPlot
        plot.ax.legend()
        plot.canvas.draw()
        self.timeSeriesTableWidget.clearContents()
        self.timeSeriesTableWidget.setRowCount(0)

    @busy
    def qTimeSeriesDoubleClicked(self, item: QtWidgets.QTableWidgetItem):
        index = item.row()
        self.workspace.timeSeriesIndex = index
        self.showTimeSeries(index)

    @restore
    def showTimeSeries(self, shownTimeSeriesIndex: int):
        timeSeries = self.workspace.timeSerieses[shownTimeSeriesIndex]
        retentionTime = self.timeSeriesUseRetentionTimeCheckBox.isChecked()
        startTime: np.datetime64 = timeSeries.time[0]
        time = None
        strTime = None
        if retentionTime:
            time = timeSeries.time - startTime

            def strTime(time: np.datetime64):
                time: datetime.timedelta = time.astype(datetime.timedelta)
                return "%.2f min" % (time.total_seconds() / 60)
        else:
            time = timeSeries.time

            def strTime(time: np.timedelta64):
                time: datetime.datetime = time.astype(datetime.datetime)
                return time.replace(microsecond=0).isoformat()
        intensity = timeSeries.intensity
        table = self.timeSeriesTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(time))
        for index, (t, i) in enumerate(zip(time, intensity)):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, strTime(t))
            setValue(1, i)

    def timeSeriesRescale(self):
        plot = self.timeSeriesPlot
        workspace = self.workspace
        if len(plot.ax.get_lines()) == 0:
            return
        l, r = plot.ax.get_xlim()
        l = np.array(matplotlib.dates.num2date(
            l).replace(tzinfo=None), dtype=np.datetime64)
        r = np.array(matplotlib.dates.num2date(
            r).replace(tzinfo=None), dtype=np.datetime64)
        b = 0
        t = 1
        for timeSeries in workspace.timeSerieses:
            rng = OrbitoolFunc.indexBetween(timeSeries.time, (l, r))
            if len(rng) > 0:
                t = max(t, timeSeries.intensity[rng].max())

        if self.timeSeriesLogScaleCheckBox.isChecked():
            t *= 10
            b = 1
        else:
            delta = 0.05 * t
            b = -delta
            t += delta
        plot.ax.set_ylim(b, t)
        plot.canvas.draw()

    @busy
    @withoutArgs
    def qTimeSeriesRescale(self):
        self.timeSeriesRescale()

    @busy
    @withoutArgs
    def qTimeSeriesLogScaleToggle(self):
        log = self.timeSeriesLogScaleCheckBox.isChecked()
        ax = self.timeSeriesPlot.ax
        ax.set_yscale('log' if log else 'linear')
        if not log:
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        self.timeSeriesRescale()

    @threadBegin
    @withoutArgs
    @savefile("Save as", "csv file(*.csv)")
    def qTimeSeriesesExport(self, path):
        withppm=self.timeSeriesesExportWithPpmCheckBox.isChecked()
        thread = QThread(OrbitoolExport.exportTimeSerieses,
                         (path, self.workspace.timeSerieses, withppm))
        thread.finished.connect(self.csvExportFinished)
        return thread

    @threadBegin
    @withoutArgs
    @savefile("Save as", "csv file(*.csv)")
    def qTimeSeriesExport(self, path):
        if self.workspace.timeSeriesIndex is None:
            raise ValueError('There is no time series shown')
        withppm=self.timeSeriesesExportWithPpmCheckBox.isChecked()
        thread = QThread(OrbitoolExport.exportTimeSerieses, (path, [
                         self.workspace.timeSerieses[self.workspace.timeSeriesIndex]], withppm))
        thread.finished.connect(self.csvExportFinished)
        return thread