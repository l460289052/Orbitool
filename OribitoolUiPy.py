# -*- coding: utf-8 -*-
import os
import datetime
import copy
from typing import Union, List, Tuple
import types
from functools import wraps
import traceback

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import psutil
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
import matplotlib.figure
import matplotlib.axes
import matplotlib.ticker
import matplotlib.animation


import OribitoolOptions
import OribitoolFormula
import OribitoolFunc
import OribitoolGuessIons

import OribitoolUi
import OribitoolClass


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
    return QThread(OribitoolFunc.multiProcess, (func, argsList, fileTime, cpu))


def showInfo(content: str, cap=None):
    QtWidgets.QMessageBox.information(
        None, cap if cap is not None else 'info', str(content))


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


def withoutArgs(func):
    @wraps(func)
    def decorator(self, *args, **kargs):
        func(self)
    return decorator


def threadBegin(func):
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

def threadEnd(setBusy=True):
    setb = setBusy if isinstance(setBusy, bool) else True
    def f(func):
        @wraps(func)
        def decorator(self, args: tuple):
            try:
                err = args[0]
                if isinstance(err, Exception):
                    raise err
                result, args = args
                func(self, result, args)
            except Exception as e:
                showInfo(str(e))
                with open('error.txt', 'a') as file:
                    print('', datetime.datetime.now(), str(e), sep='\n', file=file)
                    traceback.print_exc(file=file)
            self.rmFinished()
            if setb:
                self.setBusy(False)
        return decorator
    if isinstance(setBusy,types.FunctionType):
        return f(setBusy)
    return f


def restore(func):
    @wraps(func)
    def decorator(self, *args):
        args0, *args_ = args
        if args0 is None:
            return
        return func(self, *args)
    return decorator


def timer(func):
    @wraps(func)
    def decorator(self, *args):
        if self.busy:
            return
        return func(self, *args)
    return decorator

def openfile(caption, filter = None, multi=False, folder=False):
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
                        caption=caption, filter=filter)
                    if len(files) > 0:
                        return func(self, files)
                return forfiles
                        
        else:
            if folder:
                @wraps(func)
                def forfolder(self):
                    folder = QtWidgets.QFileDialog.getExistingDirectory(
                        caption=caption)
                    if os.path.isdir(folder):
                        return func(self, folder)
                return forfolder
            else:
                @wraps(func)
                def forfile(self):
                    file, typ = QtWidgets.QFileDialog.getOpenFileName(
                        caption=caption,filter=filter)
                    if os.path.isfile(file):
                        return func(self, file)
                return forfile
    return f

def savefile(caption, filter):
    if isinstance(caption, types.FunctionType):
        raise TypeError()
    def f(func):
        @wraps(func)
        def decorator(self):
            path, typ = QtWidgets.QFileDialog.getSaveFileName(
                caption=caption,
                initialFilter=filter,
                filter=filter,
                options=QtWidgets.QFileDialog.DontConfirmOverwrite)
            return func(self, path)
        return decorator
    return f

                


class Window(QtWidgets.QMainWindow, OribitoolUi.Ui_MainWindow):
    '''
    functions'name with q means accept user's input
    '''

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        self.setupUi(self)

        self.workspaceImportAction.triggered.connect(self.qWorkspaceImport)
        self.workspaceExportAction.triggered.connect(self.qWorkspaceExport)

        self.formulaPlusRadioButton.clicked.connect(self.qFormulaChargeToggle)
        self.formulaMinusRadioButton.clicked.connect(self.qFormulaChargeToggle)
        self.formulaApplyPushButton.clicked.connect(self.qFormulaApply)

        self.addFolderPushButton.clicked.connect(self.qAddFolder)
        self.addFilePushButton.clicked.connect(self.qAddFile)
        self.removeFilePushButton.clicked.connect(self.qRemoveFile)
        self.showFilePushButton.clicked.connect(self.qShowFileSpectra)
        self.averageSelectedPushButton.clicked.connect(
            self.qAverageSelectedFile)
        self.averageAllPushButton.clicked.connect(self.qAverageAllFile)
        self.spectra1TableWidget.itemDoubleClicked.connect(
            self.qSpectra1DoubleClicked)
        self.fitPeakPushButton.clicked.connect(
            self.qfitPeak1UseCurrentSpectrum)
        self.peak1CancelPushButton.clicked.connect(self.qPeak1RmCancel)
        self.peak1FinishPushButton.clicked.connect(self.qPeak1Finish)
        self.calibrationAddIonToolButton.clicked.connect(
            self.qCalibrationAddIon)
        self.calibrationDelIonToolButton.clicked.connect(
            self.qCalibrationRmIon)
        self.calibratePushButton.clicked.connect(self.qInitCalibration)
        self.calibrationShowedSelectedPushButton.clicked.connect(
            self.qCalibrationShowSelected)
        self.calibrationShowAllPushButton.clicked.connect(
            self.qCalibrationShowAll)
        self.calibrationFinishPushButton.clicked.connect(
            self.qCalibrationFinish)
        self.spectra2FitDefaultPushButton.clicked.connect(
            self.qSpectra2FitSpectrum)
        self.spectra2FitUseMassListPushButton.clicked.connect(
            self.qSpectra2FitUseMassList)
        self.spectrum2PeakListTableWidget.itemDoubleClicked.connect(
            self.qSpectra2PeakListDoubleClicked)
        self.spectrum2PeakOriginCheckBox.toggled.connect(
            self.qSpectra2PeakReshow)
        self.spectrum2PeakSumCheckBox.toggled.connect(
            self.qSpectra2PeakReshow)
        self.spectrum2PeakResidualCheckBox.toggled.connect(
            self.qSpectra2PeakReshow)
        self.spectrum2PeakLegendCheckBox.toggled.connect(
            self.qSpectra2PeakReshow)
        self.spectrum2PeakRefitPushButton.clicked.connect(
            self.qSpectra2PeakRefit)
        self.spectrum2PeakClosePushButton.clicked.connect(
            self.qSpectra2PeakClose)
        self.spectrum2PeakSavePushButton.clicked.connect(
            self.qSpectra2PeakSave)
        self.spectrum2PeaksAddPushButton.clicked.connect(
            self.qSpectra2PeaksAdd)
        self.spectrum2PeaksAddAllPushButton.clicked.connect(
            self.qSpectra2PeaksAddAll)
        self.massListRemovePushButton.clicked.connect(
            self.qSpectra2MassRemove)
        self.massListImportPushButton.clicked.connect(
            self.qMassListImport)
        self.massListExportPushButton.clicked.connect(
            self.qMassListExport)

        self.fileTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectra1TableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectrum1PropertyTableWidget.horizontalHeader(
        ).setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.spectrum1TableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectra2TableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectrum2PeakListTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.spectrum1Widget.setLayout(QtWidgets.QVBoxLayout())
        self.spectrum1Canvas = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.spectrum1ToolBar = NavigationToolbar2QT(
            self.spectrum1Canvas, self.spectrum1Widget)
        self.spectrum1Widget.layout().addWidget(self.spectrum1ToolBar)
        self.spectrum1Widget.layout().addWidget(self.spectrum1Canvas)
        # right class is `matplotlib.axes._subplots.AxesSubplot`, just for type hint
        self.spectrum1Ax: matplotlib.axes.Axes = self.spectrum1Canvas.figure.subplots()
        self.spectrum1Ax.autoscale(True)
        # self.spectrum1Canvas.figure.tight_layout()
        self.spectrum1Canvas.figure.subplots_adjust(
            left=0.1, right=0.999, top=0.999, bottom=0.05)
        self.spectrum1Timer = QtCore.QTimer(self)
        self.spectrum1Timer.setInterval(500)
        self.spectrum1Timer.timeout.connect(self.qSpectrum1ListFitXAxis)
        self.spectrum1Timer.start()
        self.spectrum1XAxisLeft = None

        self.peak1Widget.setLayout(QtWidgets.QVBoxLayout())
        self.peak1Canvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.peak1Widget.layout().addWidget(self.peak1Canvas)
        self.peak1Ax: matplotlib.axes.Axes = self.peak1Canvas.figure.subplots()
        self.peak1Ax.autoscale(True)
        self.peak1Canvas.mpl_connect(
            'button_press_event', self.qPeak1MouseToggle)
        self.peak1Canvas.mpl_connect(
            'button_release_event', self.qPeak1MouseToggle)
        self.peak1Canvas.mpl_connect(
            'motion_notify_event', self.qPeak1MouseMove)
        self.peak1NormLine: matplotlib.lines.Line2D = None
        self.peak1MouseStartPoint = None
        self.peak1MouseEndPoint = None
        self.peak1MouseLine: matplotlib.lines.Line2D = None
        self.peak1MouseLineAni: matplotlib.animation.FuncAnimation = None

        self.calibrationWidget.setLayout(QtWidgets.QVBoxLayout())
        self.calibrationCanvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.calibrationWidget.layout().addWidget(self.calibrationCanvas)
        self.calibrationAx: matplotlib.axes.Axes = self.calibrationCanvas.figure.subplots()
        self.calibrationAx.autoscale(True)

        self.spectrum2Widget.setLayout(QtWidgets.QVBoxLayout())
        self.spectrum2Canvas = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.spectrum2ToolBar = NavigationToolbar2QT(
            self.spectrum2Canvas, self.spectrum2Widget)
        self.spectrum2Widget.layout().addWidget(self.spectrum2ToolBar)
        self.spectrum2Widget.layout().addWidget(self.spectrum2Canvas)
        self.spectrum2Ax: matplotlib.axes.Axes = self.spectrum2Canvas.figure.subplots()
        self.spectrum2Ax.autoscale(True)
        self.spectrum2Canvas.figure.subplots_adjust(
            left=0.1, right=0.999, top=0.999, bottom=0.05)
        self.spectrum2Timer = QtCore.QTimer(self)
        self.spectrum2Timer.setInterval(1000)
        self.spectrum2Timer.timeout.connect(self.qSpectrum2ListFitXAxis)
        self.spectrum2Timer.start()
        self.spectrum2XAxisLeft = None

        self.spectrum2PeakWidget.setLayout(QtWidgets.QVBoxLayout())
        self.spectrum2PeakCanvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.spectrum2PeakWidget.layout().addWidget(self.spectrum2PeakCanvas)
        self.spectrum2PeakAx: matplotlib.axes.Axes = self.spectrum2PeakCanvas.figure.subplots()
        self.spectrum2PeakAx.autoscale(True)
        self.spectrum2PeakCanvas.figure.subplots_adjust(
            left=0.2, right=0.95, top=0.95, bottom=0.2)

        self.spectrum2PeakFitGroupBox.setHidden(True)

        self.fileList = OribitoolClass.FileList()
        self.workspace = OribitoolClass.Workspace()

        self.threads = []
        self.windows = []

        self.showFormulaOption()
        self.busy = False
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
            showInfo("wait for processing", 'busy')
            return False
        self.busy = busy
        self.widget.setDisabled(busy)
        self.progressBar.setHidden(not busy)
        return True

    def showStatus(self, fileTime: datetime.datetime, msg: str, current: int, total: int):
        showedMsg = None
        if current >= 0:
            showedMsg = self.fileList[fileTime].name + \
                '\t\t|\t' + msg + '\t|\t\t' + str(current)
            if total > 0:
                showedMsg += '/' + str(total)
                self.progressBar.setValue(round(100 * current / total))
            else:
                self.progressBar.setValue(100)
        else:
            showedMsg = msg
        self.statusbar.showMessage(showedMsg)

    @threadBegin
    @withoutArgs
    @openfile(caption="Select Work file",filter="Work file(*.OribitWork)")
    def qWorkspaceImport(self, file):
        def process(filepath, sendStatus):
            return OribitoolFunc.file2Obj(filepath)

        thread = QThread(process, (file,))
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.workspaceImportFinished)
        self.threads.append(thread)
        thread.start()

    @threadEnd
    def workspaceImportFinished(self, result, args):
        workspace: OribitoolClass.Workspace = result['workspace']
        fileTimePaths: List[Tuple[datetime.datetime, str]
                            ] = result['fileTimePaths']
        self.workspace = workspace
        self.fileTableWidget.setRowCount(len(fileTimePaths))
        fileList = self.fileList
        for index, (time, path) in enumerate(fileTimePaths):
            if os.path.exists(path):
                fileList.addFile(path)
            while time not in fileList:
                showInfo("cannot find file '%s'" % path)
                files = QtWidgets.QFileDialog.getOpenFileNames(
                    caption="Select one or more files",
                    directory='.',
                    filter="RAW files(*.RAW)")
                for path in files[0]:
                    fileList.addFile(path)
            self.showFile(time, index)
        if workspace.showedSpectra1Type is OribitoolClass.ShowedSpectraType.File:
            self.showFileSpectra1(workspace.showedSpectra1FileTime)
        elif workspace.showedSpectra1Type is OribitoolClass.ShowedSpectraType.Averaged:
            self.showAveragedSpectra1(workspace.showedAveragedSpectra1)

        self.showSpectrum1(workspace.showedSpectrum1)
        self.showPeakFitFunc(workspace.peakFitFunc)
        self.showCalibrationIon(workspace.calibrationIonList)
        self.showSpectra2(workspace.calibratedSpectra2)
        self.showSpectra2Peaks(workspace.showedSpectrum2Peaks)
        self.showMassList(workspace.massList)

    @threadBegin
    @withoutArgs
    @savefile("Save as", "Work file(*.OribitWork)")
    def qWorkspaceExport(self, path):
        workspace = self.workspace
        fileTimePaths = []
        for (time, file) in fileList.timedict.items():
            fileTimePaths.append((time, file.path))

        data = {'workspace': workspace, 'fileTimePaths': fileTimePaths}

        def process(path, data, sendStatus):
            return OribitoolFunc.obj2File(path, data)

        thread = QThread(
            process, (os.path.splitext(path)[0]+'.OribitWork', data))
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.workspaceExportFinished)
        self.threads.append(thread)
        thread.start()

    @threadEnd
    def workspaceExportFinished(self, result, args):
        pass

    @busy
    @withoutArgs
    def qFormulaChargeToggle(self):
        ionCalculator = self.workspace.ionCalculator
        if self.formulaMinusRadioButton.isChecked():
            ionCalculator['charge'] = -1
        else:
            ionCalculator['charge'] = 1
        self.showFormulaOption()

    def showFormulaOption(self, ionCalculator: OribitoolGuessIons.IonCalculator = None):
        calculator = ionCalculator if ionCalculator is not None else self.workspace.ionCalculator
        charge = calculator['charge']
        if charge == 1:
            self.formulaPlusRadioButton.setChecked(True)
        elif charge == -1:
            self.formulaMinusRadioButton.setChecked(True)
        self.formulaPpmDoubleSpinBox.setValue(calculator.errppm*1e6)
        self.formulaNitrogenRuleCheckBox.setChecked(calculator['NitrogenRule'])
        self.formulaOCRatioSpinBox.setValue(calculator['OCRatioMax'])
        self.formulaONRatioSpinBox.setValue(calculator['ONRatioMax'])
        self.formulaOSRatioSpinBox.setValue(calculator['OSRatioMax'])
        values = []

        for e in calculator['elements']:
            values.append((e, calculator[e]))
        for e in calculator['isotopes']:
            values.append((e, calculator[e]))
        values.append(('DBE', calculator['DBE']))

        table = self.formulaTableWidget
        table.setRowCount(len(values))
        for index, (_, (mi, ma)) in enumerate(values):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, mi)
            setValue(1, ma)
        values = [value for value, _ in values]
        table.setVerticalHeaderLabels(values)

    @busy
    @withoutArgs
    def qFormulaApply(self):
        calculator = self.workspace.ionCalculator
        charge = calculator['charge']

        calculator.errppm = self.formulaPpmDoubleSpinBox.value()/1e6
        calculator['NitrogenRule'] = self.formulaNitrogenRuleCheckBox.isChecked()
        calculator['OCRatioMax'] = self.formulaOCRatioSpinBox.value()
        calculator['ONRatioMax'] = self.formulaONRatioSpinBox.value()
        calculator['OSRatioMax'] = self.formulaOSRatioSpinBox.value()

        table = self.formulaTableWidget
        for index in range(table.rowCount()):
            label = table.verticalHeaderItem(index).text()

            def getValue(column):
                return table.item(index, column).text()
            mi = int(getValue(0))
            ma = int(getValue(1))
            calculator[label] = (mi, ma)

        self.showFormulaOption()

    def showFile(self, time: datetime.datetime, index: int):
        table = self.fileTableWidget

        def setValue(column: int, s: str):
            table.setItem(index, column, QtWidgets.QTableWidgetItem(s))

        def date2str(time: datetime.datetime):
            return time.strftime(r'%m/%d %X')

        f: OribitoolClass.File = self.fileList[time]
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

    @busy
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

    @busy
    @withoutArgs
    @openfile("Select one or more files","RAW files(*.RAW)")
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
        indexes = table.selectedIndexes
        indexes = [index.row() for index in indexes]
        indexes.sort(reverse=True)
        for index in indexes:
            self.fileList.rmFile(table.item(index, 3).text())
            table.removeRow(index)
        self.showFileTimeRange()

    @busy
    @withoutArgs
    def qShowFileSpectra(self):
        fileIndex = self.fileTableWidget.selectedIndexes()
        if not fileIndex:
            raise ValueError('No file was selected')
        fileIndex = fileIndex[0].row()
        filepath = self.fileTableWidget.item(fileIndex, 3).text()

        self.workspace.showedSpectra1Type = OribitoolClass.ShowedSpectraType.File
        self.workspace.showedSpectra1FileTime = self.fileList[filepath].creationDate

        self.showFileSpectra1(self.workspace.showedSpectra1FileTime)

        self.tabWidget.setCurrentWidget(self.spectra1Tab)

    @restore
    def showFileSpectra1(self, showedSpectra1FileTime: datetime.datetime):
        f: OribitoolClass.File = self.fileList[showedSpectra1FileTime]
        infoList = f.getSpectrumInfoList()

        table = self.spectra1TableWidget
        table.setRowCount(len(infoList))
        for index, info in enumerate(infoList):
            info: OribitoolClass.SpectrumInfo

            def setValue(column: int, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))

            setValue(0, info.retentionTime.total_seconds()/60)
            setValue(1, info.retentionTime.total_seconds()/60)

    @threadBegin
    @withoutArgs
    def qAverageSelectedFile(self):
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

        table = self.fileTableWidget
        fileIndexes = table.selectedIndexes()
        if not fileIndexes:
            raise ValueError('No file was selected')

        fileList = self.fileList.subList(
            [table.item(index.row(), 3).text() for index in fileIndexes])

        thread = QThread(OribitoolClass.AveragedSpectra,
                         (fileList, time, N, (startTime, endTime)))
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.averageFinished)
        self.threads.append(thread)
        thread.start()
        # thread.run()

    @threadBegin
    @withoutArgs
    def qAverageAllFile(self):
        # should calc in another thread
        workspace = self.workspace
        time = None
        N = None
        if self.averageNSpectraRadioButton.isChecked():
            N = self.averageNSpectraSpinBox.value()
        if self.averageNMinutesRadioButton.isChecked():
            time = datetime.timedelta(
                minutes=self.averageNMinutesDoubleSpinBox.value())
        startTime = self.averageStartDateTimeEdit.dateTime()
        endTime = self.averageEndDateTimeEdit.dateTime()

        thread = QThread(OribitoolClass.AveragedSpectra,
                         (copy.copy(self.fileList), time, N, (startTime, endTime)))
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.averageFinished)
        self.threads.append(thread)
        thread.start()

    @threadEnd
    def averageFinished(self, result, args):
        averagedSpectra = result

        self.workspace.showedSpectra1Type = OribitoolClass.ShowedSpectraType.Averaged
        self.workspace.showedAveragedSpectra1 = averagedSpectra

        self.showAveragedSpectra1(averagedSpectra)

        self.tabWidget.setCurrentWidget(self.spectra1Tab)

    @restore
    def showAveragedSpectra1(self, averagedSpectra: OribitoolClass.AveragedSpectra):
        table = self.spectra1TableWidget
        table.setRowCount(len(averagedSpectra))
        for index, spectrum in enumerate(averagedSpectra.spectra):
            def setValue(column: int, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))

            startTime, endTime = spectrum.timeRange
            setValue(0, startTime.strftime(r"%m.%d %H:%M:%S"))
            setValue(1, endTime.strftime(r"%m.%d %H:%M:%S"))

    @restore
    def showSpectrum1(self, spectrum: Union[OribitoolClass.Spectrum, OribitoolClass.AveragedSpectrum]):
        table = self.spectrum1TableWidget

        table.setRowCount(len(spectrum.mz))

        for index in range(len(spectrum.mz)):

            def setValue(column: int, s: str):
                table.setItem(index, column, QtWidgets.QTableWidgetItem(s))

            setValue(0, "%.6f" % (spectrum.mz[index]))
            setValue(1, "%.2f" % (spectrum.intensity[index]))

        table.resizeColumnsToContents()

        ax = self.spectrum1Ax
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        ax.yaxis.set_tick_params(rotation=45)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        ax.plot(spectrum.mz, spectrum.intensity, linewidth=1)
        self.spectrum1Canvas.draw()

    @busy
    def qSpectra1DoubleClicked(self, item: QtWidgets.QTableWidgetItem):
        workspace = self.workspace
        index = item.row()
        spectrum = None
        self.spectrum1PropertyTableWidget.clearContents()
        if workspace.showedSpectra1Type == OribitoolClass.ShowedSpectraType.File:
            f = self.fileList[workspace.showedSpectra1FileTime]
            index += f.firstScanNumber
            info = f.getSpectrumInfo(index)

            # show property
            table = self.spectrum1PropertyTableWidget
            table.setRowCount(0)

            spectrum = info.getSpectrum()
        elif workspace.showedSpectra1Type == OribitoolClass.ShowedSpectraType.Averaged:
            spectrum: OribitoolClass.AveragedSpectrum = workspace.showedAveragedSpectra1.spectra[
                index]

            # show property
            table = self.spectrum1PropertyTableWidget
            table.setRowCount(5)

            value = []
            fileList = self.fileList
            value.append(('file', fileList[spectrum.fileTime].name))
            startTime, endTime = spectrum.timeRange
            value.append(('start', startTime.strftime(r'%Y%m%d %H:%M:%S')))
            value.append(('end', endTime.strftime(r'%Y%m%d %H:%M:%S')))

            for index, (k, v) in enumerate(value):
                def setValue(column, s):
                    table.setItem(
                        index, column, QtWidgets.QTableWidgetItem(str(s)))
                setValue(0, k)
                setValue(1, v)

        self.workspace.showedSpectrum1 = spectrum
        self.showSpectrum1(spectrum)

    @timer
    def qSpectrum1ListFitXAxis(self):
        if not self.spectrum1AutoScrollCheckBox.isChecked() or self.workspace.showedSpectrum1 is None:
            return
        l, r = self.spectrum1Ax.get_xlim()
        if l != self.spectrum1XAxisLeft:
            workspace = self.workspace
            self.spectrum1XAxisLeft = l
            start,stop = OribitoolFunc.indexBetween_njit(
                workspace.showedSpectrum1.mz, (l, r))
            self.spectrum1TableWidget.verticalScrollBar().setSliderPosition(start)

    def fitPeak1PlotNormPeakWithoutDraw(self):
        if self.peak1NormLine is not None:
            self.peak1NormLine.remove()
            del self.peak1NormLine
        ax = self.peak1Ax
        normMz = np.linspace(-2e-5, 2e-5, 500)
        peakFitFunc = self.workspace.peakFitFunc
        func = peakFitFunc.func
        if func is None:
            return
        normIntensity = func.normFunc(normMz)
        lines = ax.plot(normMz, normIntensity, color='black', linewidth=3,
                        label="Fit, Res = " + str(int(func.peakResFit)))
        self.peak1NormLine = lines[-1]
        ax.legend()

    @busy
    @withoutArgs
    def qfitPeak1UseCurrentSpectrum(self):
        workspace = self.workspace
        if workspace.showedSpectrum1 is None:
            raise(ValueError())

        spectrum = workspace.showedSpectrum1
        peakFitFunc = OribitoolClass.PeakFitFunc(spectrum, 100)

        self.workspace.peakFitFunc = peakFitFunc
        self.showPeakFitFunc(peakFitFunc)

        self.peak1Canvas.draw()
        self.tabWidget.setCurrentWidget(self.peakFit1Tab)

    @restore
    def showPeakFitFunc(self, peakFitFunc: OribitoolClass.PeakFitFunc):
        ax = self.peak1Ax
        ax.clear()
        self.peak1MouseStartPoint = None
        self.peak1MouseEndPoint = None
        self.peak1MouseLine = None
        self.peak1MouseLineAni = None
        ax.xaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        for normPeak in peakFitFunc.normPeaks:
            ax.plot(normPeak[0], normPeak[1])
        self.fitPeak1PlotNormPeakWithoutDraw()

    def qPeak1MouseToggle(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button is matplotlib.backend_bases.MouseButton.LEFT and event.name == 'button_press_event':
            self.peak1MouseStartPoint = (event.xdata, event.ydata)
            self.peak1MouseEndPoint = self.peak1MouseStartPoint
            lines = self.peak1Ax.plot([], [], color='red')
            self.peak1MouseLine = lines[-1]
            self.peak1MouseLineAni = matplotlib.animation.FuncAnimation(
                self.peak1Canvas.figure, self.qPeak1PrintMouseMove, interval=20, blit=True, repeat=False)
        elif self.peak1MouseStartPoint is not None and event.name == 'button_release_event':
            workspace = self.workspace
            if workspace.peakFitFunc is not None and event.xdata is not None:
                line = (self.peak1MouseStartPoint,
                        self.peak1MouseEndPoint)
                ax = self.peak1Ax
                func = workspace.peakFitFunc
                peaks = func.normPeaks
                indexes = [index for index in range(
                    len(func.normPeaks)) if OribitoolFunc.linePeakCrossed(line, peaks[index])]
                if len(indexes) == len(peaks):
                    showInfo("couldn't remove all peaks")
                elif len(indexes) > 0:
                    func.rm(indexes)
                    indexes.reverse()
                    for index in indexes:
                        line = ax.lines.pop(index)
                        del line
                    self.fitPeak1PlotNormPeakWithoutDraw()

            self.peak1MouseLineAni._stop()
            del self.peak1MouseLineAni
            self.peak1MouseLineAni = None
            self.peak1MouseLine.remove()
            del self.peak1MouseLine
            self.peak1MouseLine = None
            self.peak1Canvas.draw()

    def qPeak1MouseMove(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button == matplotlib.backend_bases.MouseButton.LEFT:
            self.peak1MouseEndPoint = (event.xdata, event.ydata)

    def qPeak1PrintMouseMove(self, frame):
        line = self.peak1MouseLine
        if line is not None:
            start = self.peak1MouseStartPoint
            end = self.peak1MouseEndPoint
            if start is not None and end is not None:
                line.set_data([[start[0], end[0]], [start[1], end[1]]])
            return line,
        return ()

    @busy
    @withoutArgs
    def qPeak1RmCancel(self):
        peaks = self.workspace.peakFitFunc.cancel()
        ax = self.peak1Ax
        for peak in peaks:
            ax.plot(peak.mz, peak.intensity)
        self.fitPeak1PlotNormPeakWithoutDraw()
        self.peak1Canvas.draw()

    @busy
    @withoutArgs
    def qPeak1Finish(self):
        if self.workspace.peakFitFunc is not None:
            self.tabWidget.setCurrentWidget(self.calibrationTab)
        else:
            showInfo('Please fit peak first')

    @busy
    @withoutArgs
    def qCalibrationAddIon(self):
        ions = self.calibrationLineEdit.text().split(',')
        workspace = self.workspace
        ionList = workspace.calibrationIonList
        index = len(ionList)
        self.calibrationIonsTableWidget.setRowCount(index+len(ions))
        for ion in ions:
            tmp = ion.strip()
            if len(tmp) == 0:
                continue
            formula = OribitoolFormula.Formula(tmp)
            for text, f in ionList:
                if formula == f:
                    raise ValueError('There is same ion added')
            strFormulaPair = (tmp, formula)
            ionList.append(strFormulaPair)
            self.showCalibrationIonAt(index, strFormulaPair)
            index += 1
        self.calibrationIonsTableWidget.setRowCount(len(ionList))

    @restore
    def showCalibrationIon(self, ionList: List[Tuple[str, OribitoolFormula.Formula]]):
        self.calibrationIonsTableWidget.setRowCount(len(ionList))
        for index, pair in enumerate(ionList):
            self.showCalibrationIonAt(index, pair)

    def showCalibrationIonAt(self, index, strFormulaPair: (str, OribitoolFormula.Formula)):
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
        indexes = sorted([index.row() for index in indexes], reverse=True)
        table = self.calibrationIonsTableWidget
        ionList = self.workspace.calibrationIonList
        for index in indexes:
            table.removeRow(index)
            ionList.pop(index)

    @threadBegin
    @withoutArgs
    def qInitCalibration(self):
        fileList = self.fileList
        workspace = self.workspace
        peakFitFunc = workspace.peakFitFunc
        ionList = [f for _, f in workspace.calibrationIonList]
        ppm = 1
        useNIons = 3

        timeList = None
        spectraList = None
        if workspace.showedSpectra1Type is OribitoolClass.ShowedSpectraType.Averaged:
            timeList = workspace.showedAveragedSpectra1.fileTimeSorted
            spectraList = [
                workspace.showedAveragedSpectra1.fileTimeSpectraMap[time] for time in timeList]
        else:
            timeList = [workspace.showedSpectra1FileTime]
            spectraList = [[info.getSpectrum(
            ) for info in fileList[workspace.showedSpectra1FileTime].getSpectrumInfoList()]]
        argsList = [(spectra, peakFitFunc, ionList, (2,), ppm, useNIons)
                    for spectra in spectraList]

        thread = QMultiProcess(
            OribitoolClass.CalibrateMass, argsList, timeList)
        # thread = QMultiProcess(
        #     OribitoolClass.CalibrateMass, argsList, timeList,1)

        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.qInitCalibrationFinished)
        self.threads.append(thread)
        thread.start()
        # thread.run()

    def showCalibrationInfoAll(self):
        fileList = self.fileList
        workspace = self.workspace
        calibrations = [
            cali for cali in workspace.fileTimeCalibrations.values()]
        x = [cali.fileTime for cali in calibrations]

        table = self.calibrationResultTableWidget
        table.clearContents()
        table.setColumnCount(len(workspace.calibrationIonList))
        table.setHorizontalHeaderLabels(
            [s for s, _ in workspace.calibrationIonList])
        table.setRowCount(len(calibrations))
        table.setVerticalHeaderLabels(
            [time.strftime(r'%y%m%d %H') for time in x])
        data = []
        for i, cali in enumerate(calibrations):
            data.append(cali.ionsPpm)
        data: np.ndarray = np.array(data) * 1e6

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                table.setItem(
                    i, j, QtWidgets.QTableWidgetItem(format(data[i, j], ".5f")))

        ax = self.calibrationAx
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        for ionIndex in range(data.shape[1]):
            ax.plot(x, data[:, ionIndex], label='ion: ' +
                    workspace.calibrationIonList[ionIndex][0])
        ax.xaxis.set_tick_params(rotation=45)
        ax.set_ylabel('ppm')
        ax.legend()
        ax.relim()
        ax.autoscale_view(True, True, True)
        self.calibrationCanvas.draw()

    @threadEnd
    def qInitCalibrationFinished(self, result, args):
        calibrations = result
        argsList = args
        calibrations: List[OribitoolClass.CalibrateMass]
        workspace = self.workspace
        workspace.fileTimeCalibrations = dict(
            [(cali.fileTime, cali) for cali in calibrations])

        self.showCalibrationInfoAll()

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
        massCali = list(workspace.fileTimeCalibrations.values())[0] if len(workspace.fileTimeCalibrations) == 1 else \
            workspace.fileTimeCalibrations[workspace.showedAveragedSpectra1.fileTimeSorted[index]]
        ionList = workspace.calibrationIonList

        table.setRowCount(len(ionList))
        for i in range(len(ionList)):
            def setValue(column, s):
                table.setItem(i, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, ionList[i][0])
            setValue(1, massCali.ionsMz[i, 1])
            setValue(2, massCali.ionsMz[i, 0])
            setValue(3, massCali.ionsPpm[i])
            setValue(4, 'True' if i in massCali.minIndex else 'False')

        r = (50, 1000)
        X = np.linspace(*r, 1000)
        XX = massCali.func.predictPpm(X) * 1e6
        ax = self.calibrationAx
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

    @busy
    @withoutArgs
    def qCalibrationShowAll(self):
        self.showCalibrationInfoAll()

    @threadBegin
    @withoutArgs
    def qCalibrationFinish(self):
        workspace = self.workspace
        if len(workspace.fileTimeCalibrations) == 0:
            raise ValueError('please calculate calibration infomation first')
        argsList = None
        fileTime = None
        if workspace.showedSpectra1Type == OribitoolClass.ShowedSpectraType.File:
            fileTime = workspace.showedSpectra1FileTime
            massCalibrator = workspace.fileTimeCalibrations[fileTime]
            f: OribitoolClass.File = self.fileList[fileTime]

            argsList = []
            for info in f.getSpectrumInfoList():
                argsList.append((info.getSpectrum(), (f.creationDate+info.retentionTime,
                                                      f.creationDate+info.retentionTime), massCalibrator))
            fileTime = f.creationDate
        elif workspace.showedSpectra1Type == OribitoolClass.ShowedSpectraType.Averaged:
            ftmap = workspace.fileTimeCalibrations
            argsList = [(spectrum, spectrum.timeRange, ftmap[spectrum.fileTime])
                        for spectrum in workspace.showedAveragedSpectra1.spectra]
            fileTime = [
                spectrum.fileTime for spectrum in workspace.showedAveragedSpectra1.spectra]

        thread = QMultiProcess(
            OribitoolClass.CalibratedSpectrum, argsList, fileTime)
        # thread=QMultiProcess(
        #     OribitoolClass.CalibratedSpectrum, argsList, fileTime, 1)
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.qCalibrationFinished)
        self.threads.append(thread)
        thread.start()
        # thread.run()

    @threadEnd
    def qCalibrationFinished(self,  result, args):

        workspace = self.workspace
        workspace.calibratedSpectra2 = result

        self.showSpectra2(result)
        self.tabWidget.setCurrentWidget(self.spectra2Tab)

    @restore
    def showSpectra2(self, spectra: List[OribitoolClass.CalibratedSpectrum]):
        table = self.spectra2TableWidget
        table.clearContents()
        spectra = self.workspace.calibratedSpectra2
        table.setRowCount(len(spectra))
        for index, spectrum in enumerate(spectra):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, spectrum.startTime)
            setValue(1, spectrum.endTime)

    @threadBegin
    @withoutArgs
    def qSpectra2FitSpectrum(self):
        index = self.spectra2TableWidget.selectedIndexes()
        if not index:
            raise ValueError('No spectrum was selected')
        workspace = self.workspace
        index = index[0].row()
        workspace.showedSpectrum2Index = index
        spectrum: OribitoolClass.CalibratedSpectrum = workspace.calibratedSpectra2[index]
        peakFitFunc = workspace.peakFitFunc
        calc = self.workspace.ionCalculator
        fileTime = spectrum.fileTime

        # put calibrate into threads
        def process(spectrum, sendStatus):
            fittedpeaks = peakFitFunc.fitPeaks(spectrum.peaks, sendStatus)
            msg = 'calc formula'
            result = []
            length = len(fittedpeaks)
            opeak = None
            for index, fpeak in enumerate(fittedpeaks):
                sendStatus(fileTime, msg, index, length)
                speak = OribitoolClass.StandardPeak(fpeak.peakPosition, calc.calc(
                    fpeak.peakPosition), fpeak.peaksNum, opeak is not fpeak.originalPeak)
                opeak = fpeak.originalPeak
                result.append((fpeak, speak))
            for index, (_, speak) in enumerate(result):
                # need to consider other peaks' influence
                speak.formulaList = calc.calc(speak.peakPosition)
            return result

        thread = QThread(process, (spectrum, ))

        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.qSpectra2FitSelectedFinished)
        self.threads.append(thread)
        thread.start()
        # thread.run()

    @threadEnd
    def qSpectra2FitSelectedFinished(self, result, args):
        peaks: List[Tuple[OribitoolClass.FittedPeak,
                          OribitoolClass.StandardPeak]] = result

        self.workspace.showedSpectrum2Peaks = peaks
        self.showSpectra2Peaks(peaks)

    @restore
    def showSpectra2Peaks(self, peaks: List[Tuple[OribitoolClass.FittedPeak, OribitoolClass.StandardPeak]]):
        table = self.spectrum2PeakListTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(peaks))
        for index, (fpeak, speak) in enumerate(peaks):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, format(fpeak.peakPosition, '.5f'))
            setValue(1, format(fpeak.peakIntensity, '.5e'))
            setValue(2, speak.formulaList)
            setValue(3, format(fpeak.area, '.5e'))
            setValue(4, speak.subpeaks)
        workspace=self.workspace
        peakFitFunc = workspace.peakFitFunc
        spectrum = workspace.calibratedSpectra2[workspace.showedSpectrum2Index]
        fileTime=spectrum.fileTime
        def process(peaks: List[Tuple[OribitoolClass.FittedPeak, OribitoolClass.StandardPeak]], sendStatus):
            length = len(peaks)
            mz = []
            intensity = []
            residual=[]
            opeak = None
            omz = None
            ointensity = None
            msg="calc the residual"
            for index, (fpeak, speak) in enumerate(peaks):
                sendStatus(fileTime, msg, index, length)
                if opeak != fpeak.originalPeak:
                    opeak=fpeak.originalPeak
                    omz = opeak.mz
                    ointensity = opeak.intensity
                    mz.append(omz)
                    intensity.append(ointensity)
                    ointensity=ointensity.copy()
                    residual.append(ointensity)
                ointensity -= peakFitFunc.func._funcFit(omz, *fpeak.fittedParam)
            sendStatus(fileTime, msg, index, length)
            mz = np.concatenate(mz)
            intensity = np.concatenate(intensity)
            residual = np.concatenate(residual)
            return mz, intensity, residual
        thread = QThread(process, (peaks, ))
        self.threads.append(thread)
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.showSpectra2PeakFinished)
        thread.start()          
        # thread.run()          
                


    @threadEnd(False)
    def showSpectra2PeakFinished(self, result, args):
        mz, intensity, residual = result
        ax = self.spectrum2Ax
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        ax.yaxis.set_tick_params(rotation=45)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        workspace=self.workspace
        ax.plot(mz, intensity, color='black', linewidth=1)
        ax.plot(mz, residual, color='red', linewidth=0.5, label='residual')
        ax.legend()
        workspace = self.workspace
        spectrum = workspace.calibratedSpectra2[workspace.showedSpectrum2Index]
        mi = spectrum.mz.min()
        ma = spectrum.mz.max()
        ll, lr = ax.get_xlim()
        if ll > mi:
            ll = mi
        if lr < ma:
            lr = ma
        ax.set_xlim(ll,lr)

        self.spectrum2Canvas.draw()

    @timer
    def qSpectrum2ListFitXAxis(self):
        if self.busy:
            return
        if not self.spectrum2AutoScrollCheckBox.isChecked() or self.workspace.showedSpectrum2Peaks is None:
            return
        ax = self.spectrum2Ax
        l, r = ax.get_xlim()
        if l == self.spectrum2XAxisLeft:
            return
        self.spectrum2XAxisLeft = l

        workspace = self.workspace
        peaks = workspace.showedSpectrum2Peaks
        r: range = OribitoolFunc.indexBetween(peaks, (l, r), method=(
            lambda peaks, index: peaks[index][1].peakPosition))
        self.spectrum2PeakListTableWidget.verticalScrollBar().setSliderPosition(r.start)
        
        yi,ya=ax.get_ylim()
        peaks = peaks[r.start:r.stop]
        def show(fpeak:OribitoolClass.FittedPeak):
            i = fpeak.peakIntensity
            return i > yi and i < ya
        peaks = [peak for peak in peaks if show(peak[0])]
        peakIntensities = np.array([fpeak.peakIntensity for fpeak, _ in peaks])

        indexes = np.flip(peakIntensities.argsort())

        annotations=[child for child in ax.get_children() if isinstance(child, matplotlib.text.Annotation)]
        for i in range(len(annotations)):
            ann=annotations.pop()
            ann.remove()
            del ann
        
        cnt=0
        for index in indexes:
            fpeak, speak = peaks[index]
            if len(speak.formulaList) == 0:
                continue
            opeak = fpeak.originalPeak
            i = OribitoolFunc.indexNearest_njit(opeak.mz, fpeak.peakPosition)
            position = opeak.mz[i]
            intensity = opeak.intensity[i]
            ax.annotate(','.join([str(f) for f in speak.formulaList]),
                xy=(position, intensity), xytext=(fpeak.peakPosition, fpeak.peakIntensity),
                arrowprops={"arrowstyle": "-", "alpha": 0.5})
            cnt += 1
            if cnt == 5:
                break
        self.spectrum2Canvas.draw()
            

    @busy
    def qSpectra2PeakListDoubleClicked(self, item: QtWidgets.QTableWidgetItem):
        index = item.row()
        workspace = self.workspace
        peaks = workspace.showedSpectrum2Peaks
        fpeak = peaks[index][0]
        opeak = fpeak.originalPeak

        self.spectrum2PeakNumSpinBox.setValue(fpeak.peaksNum)

        start = index
        while not peaks[start][1].isStart:
            start -= 1
        end = start + 1
        length=len(peaks)
        while end < length and not peaks[end][1].isStart:
            end += 1
        workspace.showedSpectra2PeakRange = range(start, end)
        workspace.showedSpectra2Peak = peaks[start:end]

        self.showSpectra2Peak(workspace.showedSpectra2Peak)

    @restore
    def showSpectra2Peak(self, showedSpectra2Peak: List[Tuple[OribitoolClass.FittedPeak, OribitoolClass.StandardPeak]]):
        showOrigin = self.spectrum2PeakOriginCheckBox.isChecked()
        showSum = self.spectrum2PeakSumCheckBox.isChecked()
        showResidual = self.spectrum2PeakResidualCheckBox.isChecked()
        showLegend = self.spectrum2PeakLegendCheckBox.isChecked()

        workspace = self.workspace
        opeak = showedSpectra2Peak[0][0].originalPeak
        ax = self.spectrum2PeakAx
        ax.clear()
        ax.axhline(color='black', linewidth=0.5)
        if showOrigin:
            ax.plot(opeak.mz, opeak.intensity, label='origin',
                    linewidth=2, color='black')

        sumIntensity = np.zeros_like(opeak.intensity) if showSum else None
        diffIntensity = opeak.intensity.copy() if showResidual else None

        table = self.spectrum2PeakPropertyTableWidget

        table.setRowCount(len(showedSpectra2Peak))

        peakFitFunc = workspace.peakFitFunc

        for index, (fpeak, speak) in enumerate(showedSpectra2Peak):
            ax.plot(fpeak.mz, fpeak.intensity, label='fitted peak %d' %
                    index, linewidth=1.5)

            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))

            setValue(0, fpeak.peakPosition)
            setValue(1, fpeak.peakIntensity)
            setValue(2, ', '.join([str(f) for f in speak.formulaList]))

            if showSum or showResidual:
                tmpItensity = peakFitFunc.func._funcFit(
                    opeak.mz, *fpeak.fittedParam)
                if showSum:
                    sumIntensity += tmpItensity
                if showResidual:
                    diffIntensity -= tmpItensity

        if len(showedSpectra2Peak) > 1:
            if showSum:
                ax.plot(opeak.mz, sumIntensity,
                        label='fitted peak sum', linewidth=1.5)
        if showResidual:
            ax.plot(opeak.mz, diffIntensity, label='peak diff', linewidth=1.5)

        ax.xaxis.set_tick_params(rotation=15)
        ax.yaxis.set_tick_params(rotation=60)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        if showLegend:
            ax.legend()
        ax.set_xlim(opeak.mz.min(),opeak.mz.max())

        table = self.spectrum2PeakTableWidget
        table.setRowCount(len(opeak.mz))
        for index in range(len(opeak.mz)):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, opeak.mz[index])
            setValue(1, opeak.intensity[index])

        self.spectrum2PeakFitGroupBox.setHidden(False)
        self.spectrum2Widget.setHidden(True)

    @busy
    @withoutArgs
    def qSpectra2PeakReshow(self):
        self.showSpectra2Peak(self.workspace.showedSpectra2Peak)

    @busy
    @withoutArgs
    def qSpectra2PeakRefit(self):
        num = self.spectrum2PeakNumSpinBox.value()
        workspace = self.workspace
        peaks = workspace.showedSpectra2Peak
        opeak: OribitoolClass.CalibratedPeak = peaks[0][0].originalPeak
        fittedpeaks = workspace.peakFitFunc.fitPeak(opeak, num, force=True)
        calc = workspace.ionCalculator
        isStart = True
        peaks.clear()
        for i, fpeak in enumerate(fittedpeaks):
            speak = OribitoolClass.StandardPeak(fpeak.peakPosition, calc.calc(
                fpeak.peakPosition), fpeak.peaksNum, isStart)
            peaks.append((fpeak, speak))
            isStart = False

        for _, speak in peaks:
            speak.formulaList = calc.calc(speak.peakPosition)

        self.showSpectra2Peak(peaks)

    @busy
    @withoutArgs
    def qSpectra2PeakClose(self):
        self.spectrum2PeakFitGroupBox.setHidden(True)
        self.spectrum2Widget.setHidden(False)

    @busy
    @withoutArgs
    def qSpectra2PeakSave(self):
        workspace = self.workspace
        calc = workspace.ionCalculator
        showedSpectrum2Peaks = workspace.showedSpectrum2Peaks
        r = workspace.showedSpectra2PeakRange
        showedSpectra2Peak = workspace.showedSpectra2Peak

        table=self.spectrum2PeakPropertyTableWidget
        for index, (fpeak, speak) in enumerate(showedSpectra2Peak):
            strformula=table.item(index,2).text()
            if strformula != ', '.join([str(f) for f in speak.formulaList]):
                l = []
                for s in strformula.split(','):
                    ss = s.strip()
                    if len(ss) == 0:
                        continue
                    l.append(OribitoolFormula.Formula(ss))
                speak.formulaList = l

        for i in r:
            showedSpectrum2Peaks.pop(r.start)
        for peak in reversed(showedSpectra2Peak):
            showedSpectrum2Peaks.insert(r.start, peak)
            speak = peak[1]
            speak.handled = True
        for _, speak in showedSpectrum2Peaks:
            if not speak.handled:
                speak.formulaList = calc.calc(speak.peakPosition)

        self.showSpectra2Peaks(showedSpectrum2Peaks)
        self.spectrum2PeakFitGroupBox.setHidden(True)
        self.spectrum2Widget.setHidden(False)

    @busy
    @withoutArgs
    def qSpectra2FitUseMassList(self):
        index = self.spectra2TableWidget.selectedIndexes()
        if not index:
            raise ValueError('No spectrum was selected')
        ppm = 1*1e-6
        workspace = self.workspace
        index = index[0].row()
        workspace.showedSpectrum2Index = index
        spectrum: OribitoolClass.CalibratedSpectrum = workspace.calibratedSpectra2[index]
        massList: OribitoolClass.MassList = workspace.massList
        peakFitFunc = workspace.peakFitFunc
        calc = self.workspace.ionCalculator

        thread = QThread(massList.fit, (spectrum, peakFitFunc, ppm))
        thread.sendStatus.connect(self.showStatus)
        thread.finished.connect(self.qSpectra2FitSelectedFinished)
        self.threads.append(thread)
        thread.start()
        # thread.run()

    @busy
    @withoutArgs
    def qSpectra2PeaksAdd(self):
        indexes = self.spectrum2PeakListTableWidget.selectedIndexes()
        workspace = self.workspace
        if workspace.massList is None:
            workspace.massList = OribitoolClass.MassList()
        massList = workspace.massList
        peaks = workspace.showedSpectrum2Peaks
        toBeAdded:List[OribitoolClass.StandardPeak] = [peaks[index.row()][1] for index in indexes]
        massList.addPeaks(toBeAdded)
        self.showMassList(massList)

    @busy
    @withoutArgs
    def qSpectra2PeaksAddAll(self):
        workspace = self.workspace
        if workspace.massList is None:
            workspace.massList = OribitoolClass.MassList()
        massList = workspace.massList
        peaks = workspace.showedSpectrum2Peaks
        massList.addPeaks([speak for _, speak in peaks])
        self.showMassList(massList)

    @restore
    def showMassList(self, massList: OribitoolClass.MassList):
        workspace = self.workspace
        table = self.massListTableWidget
        table.clearContents()
        table.setRowCount(len(massList))
        for index, speak in enumerate(massList):
            def setValue(column, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))
            setValue(0, speak.peakPosition)
            setValue(1, ', '.join([str(f) for f in speak.formulaList]))
            setValue(2, speak.subpeaks)

    @busy
    @withoutArgs
    def qSpectra2MassRemove(self):
        table=self.massListTableWidget
        indexes = table.selectedIndexes()
        indexes = [index.row() for index in indexes]
        indexes.sort(reverse=True)
        massList = self.workspace.massList
        for index in indexes:
            massList.popPeaks(index)
            table.removeRow(index)


    @busy
    @withoutArgs
    @openfile("Select Mass list","Mass list file(*.OribitMassList)")
    def qMassListImport(self,file):
        workspace = self.workspace
        massList: OribitoolClass = OribitoolFunc.file2Obj(file)
        if not isinstance(massList, OribitoolClass.MassList):
            raise ValueError('wrong file')
        workspace.massList = massList
        self.showMassList(massList)

    @busy
    @withoutArgs
    @savefile("Save as","Mass list file(*.OribitMassList)")
    def qMassListExport(self, path):
        OribitoolFunc.obj2File(path, self.workspace.massList)
