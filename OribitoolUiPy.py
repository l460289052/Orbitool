# -*- coding: utf-8 -*-
import os
import datetime
import copy
from typing import Union, List

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

import OribitoolUi
import OribitoolClass


class QThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, str, int, int)

    def __init__(self, func, args: tuple):
        super(QtCore.QThread, self).__init__(None)
        self.func = func
        self.args = args

    def run(self):
        result = self.func(*self.args, self.sendStatusFunc)
        self.finished.emit((result, self.args))

    def sendStatusFunc(self, filepath, msg, index, length):
        self.sendStatus.emit(filepath, msg, index, length)


def QMultiProcess(func, argsList: list, filepath: Union[list, str], cpu=None) -> QThread:
    return QThread(OribitoolFunc.multiProcess, (func, argsList, filepath, cpu))


def showInfo(content: str, cap=None):
    QtWidgets.QMessageBox.information(
        None, cap if cap is not None else 'info', str(content))


class Window(QtWidgets.QMainWindow, OribitoolUi.Ui_MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        self.setupUi(self)

        self.addFolderPushButton.clicked.connect(self.qAddFolder)
        self.addFilePushButton.clicked.connect(self.qAddFile)
        self.removeFilePushButton.clicked.connect(self.qRemoveFile)
        self.showFilePushButton.clicked.connect(self.qShowFileSpectra)
        self.averageSelectedPushButton.clicked.connect(
            self.qAverageSelectedFile)
        self.averageAllPushButton.clicked.connect(self.qAverageAllFile)
        self.spectra1TableWidget.itemDoubleClicked.connect(
            self.qSpectra1DoubleClicked)
        self.fitPeakPushButton.clicked.connect(self.qfitPeak1UseCurrentSpectrum)
        self.peakFit1CancelPushButton.clicked.connect(self.qPeakFitRmCancel)
        self.peakFit1FinishPushButton.clicked.connect(self.qPeakFit1Finish)
        self.calibrationAddIonToolButton.clicked.connect(
            self.qCalibrationAddIon)
        self.calibrationDelIonToolButton.clicked.connect(
            self.qCalibrationRmIon)
        self.calibratePushButton.clicked.connect(self.qInitCalibration)
        self.calibrationShowedSelectedPushButton.clicked.connect(self.qCalibrationShowSelected)
        self.calibrationShowAllPushButton.clicked.connect(self.qCalibrationShowAll)
        self.calibrationFinishPushButton.clicked.connect(self.qCalibrationFinish)

        self.fileTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectra1TableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.spectrum1PropertyTableWidget.horizontalHeader(
        ).setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.spectrum1TableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.spectra1Widget.setLayout(QtWidgets.QVBoxLayout())
        self.spectra1Canvas = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.spectra1ToolBar = NavigationToolbar2QT(
            self.spectra1Canvas, self.spectra1Widget)
        self.spectra1Widget.layout().addWidget(self.spectra1ToolBar)
        self.spectra1Widget.layout().addWidget(self.spectra1Canvas)
        # right class is `matplotlib.axes._subplots.AxesSubplot`, just for type hint
        self.spectra1Ax: matplotlib.axes.Axes = self.spectra1Canvas.figure.subplots()
        self.spectra1Ax.autoscale(True)
        # self.spectra1Canvas.figure.tight_layout()
        self.spectra1Canvas.figure.subplots_adjust(
            left=0.1, right=0.999, top=0.999, bottom=0.05)

        self.peakFit1Widget.setLayout(QtWidgets.QVBoxLayout())
        self.peakFit1Canvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.peakFit1Widget.layout().addWidget(self.peakFit1Canvas)
        self.peakFit1Ax: matplotlib.axes.Axes = self.peakFit1Canvas.figure.subplots()
        self.peakFit1Ax.autoscale(True)
        self.peakFit1Canvas.mpl_connect(
            'button_press_event', self.qPeakFit1MouseToggle)
        self.peakFit1Canvas.mpl_connect(
            'button_release_event', self.qPeakFit1MouseToggle)
        self.peakFit1Canvas.mpl_connect(
            'motion_notify_event', self.qPeakFit1MouseMove)
        self.peakFit1NormLine: matplotlib.lines.Line2D = None
        self.peakFit1MouseStartPoint = None
        self.peakFit1MouseEndPoint = None
        self.peakFit1MouseLine: matplotlib.lines.Line2D = None
        self.peakFit1MouseLineAni: matplotlib.animation.FuncAnimation = None

        self.calibrationWidget.setLayout(QtWidgets.QVBoxLayout())
        self.calibrationCanvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.calibrationWidget.layout().addWidget(self.calibrationCanvas)
        self.calibrationAx: matplotlib.axes.Axes = self.calibrationCanvas.figure.subplots()
        self.calibrationAx.autoscale(True)

        self.fileList = OribitoolClass.FileList()
        self.workspace = OribitoolClass.Workspace()

        self.threads = []
        self.windows = []

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

    def qSetBusy(self, busy=True):
        if self.busy and busy:
            showInfo("wait for processing", 'busy')
            return False
        self.busy = busy
        self.widget.setDisabled(busy)
        self.progressBar.setHidden(not busy)
        return True

    def qShowStatus(self, filepath, msg: str, current: int, total: int):
        showedMsg = None
        if current >= 0:
            showedMsg = self.fileList.filedict[filepath].name + \
                '\t\t|\t' + msg + '\t|\t\t' + str(current)
            if total > 0:
                showedMsg += '/' + str(total)
                self.progressBar.setValue(round(100 * current / total))
            else:
                self.progressBar.setValue(100)
        else:
            showedMsg = msg
        self.statusbar.showMessage(showedMsg)

    def qShowFile(self, f: OribitoolClass.FileHeader, index: int):
        table = self.fileTableWidget

        def setValue(column: int, s: str):
            table.setItem(index, column, QtWidgets.QTableWidgetItem(s))

        def date2str(time: datetime.datetime):
            return time.strftime(r'%m/%d %X')

        setValue(0, os.path.split(f)[1])
        fh: OribitoolClass.FileHeader = self.fileList.filedict[f].header
        setValue(1, date2str(fh.creationDate + fh.startTime))
        setValue(2, date2str(fh.creationDate + fh.endTime))
        setValue(3, f)

    def qShowFileTimeRange(self):
        timeRange = self.fileList.timeRange()
        if timeRange:
            self.averageStartDateTimeEdit.setDateTime(timeRange[0])
            self.averageEndDateTimeEdit.setDateTime(timeRange[1])
        else:
            now = datetime.datetime.now()
            self.averageStartDateTimeEdit.setDateTime(now)
            self.averageEndDateTimeEdit.setDateTime(now)

    def qAddFolder(self):
        if not self.qSetBusy(True):
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            caption="Select one folder")
        table = self.fileTableWidget
        try:
            files = self.fileList.addFileFromFolder(
                folder, self.recurrenceCheckBox.isChecked(), '.raw')
            count = table.rowCount()
            table.setRowCount(count+len(files))
            for index, f in enumerate(files):
                self.qShowFile(f, count+index)

        except ValueError as e:
            showInfo('file "%s" and "%s" have crossed scan time' %
                     (e.args[0], e.args[1]), 'Error')
            self.fileList.clear()
            table.clearContents()
            table.setRowCount(0)

        # except:
        #     pass

        self.qShowFileTimeRange()
        self.qSetBusy(False)

    def qAddFile(self):
        if not self.qSetBusy(True):
            return
        try:
            files = QtWidgets.QFileDialog.getOpenFileNames(
                caption="Select one or more files",
                directory='.',
                filter="RAW files(*.RAW)")

            addedFiles = []
            for f in files[0]:
                if self.fileList.addFile(f):
                    addedFiles.append(f)

            table = self.fileTableWidget
            count = table.rowCount()
            table.setRowCount(count+len(addedFiles))
            for index, f in enumerate(addedFiles):
                self.qShowFile(f, count+index)

        except ValueError as e:
            showInfo('file "%s" and "%s" have crossed scan time' %
                     (e.args[0], e.args[1]), 'Error')

        self.qShowFileTimeRange()
        self.qSetBusy(False)

    def qRemoveFile(self):
        if not self.qSetBusy(True):
            return
        table = self.fileTableWidget
        indexes = table.selectedIndexes
        indexes = [index.row() for index in indexes]
        indexes.sort(reverse=True)
        for index in indexes:
            self.fileList.rmFile(table.item(index, 3).text())
            table.removeRow(index)
        self.qShowFileTimeRange()
        self.qSetBusy(False)

    def qShowFileSpectra(self):
        if not self.qSetBusy(True):
            return
        try:
            fileIndex = self.fileTableWidget.selectedIndexes()
            if not fileIndex:
                raise ValueError('No file was selected')
            fileIndex = fileIndex[0].row()
            filepath = self.fileTableWidget.item(fileIndex, 3).text()
            f: OribitoolClass.File = self.fileList.filedict[filepath]
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

            self.workspace.showedSpectra1Type = OribitoolClass.ShowedSpectraType.File
            self.workspace.showedSpectra1Filepath = f.path

            self.tabWidget.setCurrentWidget(self.spectra1Tab)

        except ValueError as v:
            showInfo(str(v))
        self.qSetBusy(False)

    def qAverageSelectedFile(self):
        if not self.qSetBusy(True):
            return
        try:
            workspace = self.workspace
            time = None
            N = None
            if self.averageNSpectraRadioButton.isChecked():
                N = self.averageNSpectraSpinBox.value()
            if self.averageNMinutesRadioButton.isChecked():
                time = datetime.timedelta(
                    minutes=self.averageNMinutesDoubleSpinBox.value())

            table = self.fileTableWidget
            fileIndexes = table.selectedIndexes()
            if not fileIndexes:
                raise ValueError('No file was selected')

            fileList = self.fileList.subList(
                [table.item(index.row(), 3).text() for index in fileIndexes])

            thread = QThread(OribitoolClass.AveragedSpectra,
                             (fileList, time, N))
            thread.sendStatus.connect(self.qShowStatus)
            thread.finished.connect(self.qAverageFinished)
            self.threads.append(thread)
            thread.start()
        except ValueError as v:
            showInfo(str(v))
            self.qSetBusy(False)

    def qAverageAllFile(self):
        if not self.qSetBusy(True):
            return
        try:
            # should calc in another thread
            workspace = self.workspace
            time = None
            N = None
            if self.averageNSpectraRadioButton.isChecked():
                N = self.averageNSpectraSpinBox.value()
            if self.averageNMinutesRadioButton.isChecked():
                time = datetime.timedelta(
                    minutes=self.averageNMinutesDoubleSpinBox.value())

            thread = QThread(OribitoolClass.AveragedSpectra,
                             (copy.copy(self.fileList), time, N))
            thread.sendStatus.connect(self.qShowStatus)
            thread.finished.connect(self.qAverageFinished)
            self.threads.append(thread)
            thread.start()

        except ValueError as v:
            showinfo(str(v))
            self.qSetBusy(False)

    def qAverageFinished(self, args):
        result, args = args
        averagedSpectra = result

        table = self.spectra1TableWidget
        table.setRowCount(len(averagedSpectra))
        for index, spectrum in enumerate(averagedSpectra.spectra):
            def setValue(column: int, s):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(s)))

            startTime, endTime = spectrum.timeRange
            setValue(0, startTime.strftime(r"%m.%d %H:%M:%S"))
            setValue(1, endTime.strftime(r"%m.%d %H:%M:%S"))

        self.workspace.showedSpectra1Type = OribitoolClass.ShowedSpectraType.Averaged
        self.workspace.showedAveragedSpectra1 = averagedSpectra

        self.tabWidget.setCurrentWidget(self.spectra1Tab)

        self.rmFinished()
        self.qSetBusy(False)

    def qShowSpectrum1(self, spectrum: Union[OribitoolClass.Spectrum, OribitoolClass.AveragedSpectrum]):
        table = self.spectrum1TableWidget

        table.setRowCount(len(spectrum.mz))

        for index in range(len(spectrum.mz)):

            def setValue(column: int, s: str):
                table.setItem(index, column, QtWidgets.QTableWidgetItem(s))

            setValue(0, "%.6f" % (spectrum.mz[index]))
            setValue(1, "%.2f" % (spectrum.intensity[index]))

        table.resizeColumnsToContents()
        self.workspace.showedSpectrum1 = spectrum

    def qSpectra1DoubleClicked(self, item: QtWidgets.QTableWidgetItem):
        if not self.qSetBusy(True):
            return
        workspace = self.workspace
        index = item.row()
        spectrum = None
        self.spectrum1PropertyTableWidget.clearContents()
        if workspace.showedSpectra1Type == OribitoolClass.ShowedSpectraType.File:
            f = self.fileList.filedict[workspace.showedSpectra1Filepath]
            index += f.header.firstScanNumber
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
            filedict = self.fileList.filedict
            for path in spectrum.filepaths:
                value.append(('files', filedict[path].name))
            startTime, endTime = spectrum.timeRange
            value.append(('start', startTime.strftime(r'%Y%m%d %H:%M:%S')))
            value.append(('end', endTime.strftime(r'%Y%m%d %H:%M:%S')))

            for index, (k, v) in enumerate(value):
                def setValue(column, s):
                    table.setItem(
                        index, column, QtWidgets.QTableWidgetItem(str(s)))
                setValue(0, k)
                setValue(1, v)

        # show spectrum

        self.qShowSpectrum1(spectrum)

        self.spectra1Ax.clear()
        self.spectra1Ax.axhline(color='black', linewidth=0.5)
        self.spectra1Ax.yaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter(r"%.1e"))
        self.spectra1Ax.plot(spectrum.mz, spectrum.intensity, linewidth=1)
        self.spectra1Canvas.draw()

        self.qSetBusy(False)

    def qfitPeak1PlotNormPeakWithoutDraw(self):
        if self.peakFit1NormLine is not None:
            self.peakFit1NormLine.remove()
            del self.peakFit1NormLine
        ax = self.peakFit1Ax
        normMz = np.linspace(-2e-5, 2e-5, 500)
        peakFitFunc = self.workspace.peakFitFunc
        func = peakFitFunc.func
        if func is None:
            return
        normIntensity = func.normFunc(normMz)
        lines = ax.plot(normMz, normIntensity, color='black', linewidth=3,
                        label="Fit, Res = " + str(int(func.peakResFit)))
        self.peakFit1NormLine = lines[-1]
        ax.legend()

    def qfitPeak1UseCurrentSpectrum(self):
        if not self.qSetBusy(True):
            return
        try:
            workspace = self.workspace
            if workspace.showedSpectrum1 is None:
                raise(ValueError())

            spectrum = workspace.showedSpectrum1
            peakFitFunc = OribitoolClass.PeakFitFunc(spectrum, 100)

            ax = self.peakFit1Ax
            ax.clear()
            self.peakFit1MouseStartPoint = None
            self.peakFit1MouseEndPoint = None
            self.peakFit1MouseLine = None
            self.peakFit1MouseLineAni = None
            ax.xaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
            for normPeak in peakFitFunc.normPeaks:
                normPeak: OribitoolClass.Peak
                ax.plot(normPeak.mz, normPeak.intensity)

            self.workspace.peakFitFunc = peakFitFunc
            self.qfitPeak1PlotNormPeakWithoutDraw()

            self.peakFit1Canvas.draw()
            self.tabWidget.setCurrentWidget(self.peakFit1Tab)

        except ValueError as e:
            pass
        self.qSetBusy(False)

    def qPeakFit1MouseToggle(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button is matplotlib.backend_bases.MouseButton.LEFT and event.name == 'button_press_event':
            self.peakFit1MouseStartPoint = (event.xdata, event.ydata)
            self.peakFit1MouseEndPoint = self.peakFit1MouseStartPoint
            lines = self.peakFit1Ax.plot([], [], color='red')
            self.peakFit1MouseLine = lines[-1]
            self.peakFit1MouseLineAni = matplotlib.animation.FuncAnimation(
                self.peakFit1Canvas.figure, self.qPeakFit1PrintMouseMove, interval=20, blit=True, repeat=False)
        elif self.peakFit1MouseStartPoint is not None and event.name == 'button_release_event':
            workspace = self.workspace
            if workspace.peakFitFunc is not None and event.xdata is not None:
                line = (self.peakFit1MouseStartPoint, self.peakFit1MouseEndPoint)
                ax = self.peakFit1Ax
                func = workspace.peakFitFunc
                peaks = func.normPeaks
                indexes = [index for index in range(
                    len(func.normPeaks)) if OribitoolFunc.linePeakCrossed(line, peaks[index])]
                if len(indexes) == len(peaks):
                    showInfo("couldn't delete all peaks")
                elif len(indexes) > 0:
                    func.rm(indexes)
                    indexes.reverse()
                    for index in indexes:
                        line = ax.lines.pop(index)
                        del line
                    self.qfitPeak1PlotNormPeakWithoutDraw()

            self.peakFit1MouseLineAni._stop()
            del self.peakFit1MouseLineAni
            self.peakFit1MouseLineAni = None
            self.peakFit1MouseLine.remove()
            del self.peakFit1MouseLine
            self.peakFit1MouseLine = None
            self.peakFit1Canvas.draw()

    def qPeakFit1MouseMove(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button == matplotlib.backend_bases.MouseButton.LEFT:
            self.peakFit1MouseEndPoint = (event.xdata, event.ydata)

    def qPeakFit1PrintMouseMove(self, frame):
        line = self.peakFit1MouseLine
        if line is not None:
            start = self.peakFit1MouseStartPoint
            end = self.peakFit1MouseEndPoint
            if start is not None and end is not None:
                line.set_data([[start[0], end[0]], [start[1], end[1]]])
            return line,
        return ()

    def qPeakFitRmCancel(self):
        peaks = self.workspace.peakFitFunc.cancel()
        ax = self.peakFit1Ax
        for peak in peaks:
            ax.plot(peak.mz, peak.intensity)
        self.qfitPeak1PlotNormPeakWithoutDraw()
        self.peakFit1Canvas.draw()

    def qPeakFit1Finish(self):
        if self.workspace.peakFitFunc is not None:
            self.tabWidget.setCurrentWidget(self.calibrationTab)
        else:
            showInfo('Please fit peak first')

    def qCalibrationAddIon(self):
        if not self.qSetBusy(True):
            return
        try:
            ions = self.calibrationLineEdit.text().split(',')
            for ion in ions:
                tmp = ion.strip()
                if len(tmp) == 0:
                    continue
                formula = OribitoolFormula.Formula(tmp)
                workspace = self.workspace
                ionList = workspace.calibrationIonList
                for text, f in ionList:
                    if formula == f:
                        raise ValueError('There is same ion added')
                ionList.append((tmp, formula))
                table = self.calibrationIonsTableWidget
                row = table.rowCount()

                def setValue(column, s):
                    table.setItem(
                        row, column, QtWidgets.QTableWidgetItem(str(s)))
                table.setRowCount(table.rowCount()+1)
                setValue(0, ion)
                setValue(1, formula.mass())

        except ValueError as e:
            showInfo(str(e))
        self.qSetBusy(False)

    def qCalibrationRmIon(self):
        if not self.qSetBusy(True):
            return
        try:
            indexes = self.calibrationIonsTableWidget.selectedIndexes()
            indexes = sorted([index.row() for index in indexes], reverse=True)
            table = self.calibrationIonsTableWidget
            ionList = self.workspace.calibrationIonList
            for index in indexes:
                table.removeRow(index)
                ionList.pop(index)

        except ValueError as e:
            showInfo(str(e))
        self.qSetBusy(False)

    def qInitCalibration(self):
        if not self.qSetBusy(True):
            return
        try:
            fileList = self.fileList
            workspace = self.workspace
            peakFitFunc = workspace.peakFitFunc
            ionList = [f for _, f in workspace.calibrationIonList]
            ppm = 1
            useNIons = 3

            pathList = None
            spectraList = None
            if workspace.showedSpectra1Type is OribitoolClass.ShowedSpectraType.Averaged:
                pathList = workspace.showedAveragedSpectra1.filepathTimeSorted
                spectraList = [
                    workspace.showedAveragedSpectra1.filepathSpectraMap[path] for path in pathList]
            else:
                pathList = [workspace.showedSpectra1Filepath]
                spectraList = [[info.getSpectrum(
                ) for info in fileList.filedict[workspace.showedSpectra1Filepath].getSpectrumInfoList()]]
            argsList = [(spectra, peakFitFunc, ionList, (2,), ppm, useNIons)
                        for spectra in spectraList]

            thread = QMultiProcess(
                OribitoolClass.CalibrateMass, argsList, pathList, 1)

            thread.sendStatus.connect(self.qShowStatus)
            thread.finished.connect(self.qInitCalibrationFinished)
            self.threads.append(thread)
            thread.start()
            # thread.run()

        except ValueError as e:
            showInfo(str(e))
            self.qSetBusy(False)

    def qShowCalibrationAll(self):
        fileList = self.fileList
        workspace = self.workspace
        calibrations=[cali for cali in workspace.fileCalibrations.values()]
        x = [fileList.filedict[cali.filepath].header.creationDate for cali in calibrations]

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
                    i, j, QtWidgets.QTableWidgetItem(format(data[i,j],".5f")))

        ax = self.calibrationAx
        ax.clear()
        ax.axhline(color='black',linewidth=0.5)
        for ionIndex in range(data.shape[1]):
            ax.plot(x, data[:, ionIndex], label='ion: ' +
                    workspace.calibrationIonList[ionIndex][0])
        ax.xaxis.set_tick_params(rotation=45)
        ax.set_ylabel('ppm')
        ax.legend()
        ax.relim()
        ax.autoscale_view(True,True,True)
        self.calibrationCanvas.draw()

    def qInitCalibrationFinished(self, args):
        calibrations, argsList = args
        calibrations: List[OribitoolClass.CalibrateMass]
        workspace = self.workspace
        workspace.fileCalibrations = dict(
            [(cali.filepath, cali) for cali in calibrations])

        self.qShowCalibrationAll()

        self.rmFinished()
        self.qSetBusy(False)

    def qCalibrationShowSelected(self):
        
        workspace=self.workspace
        table = self.calibrationResultTableWidget
        indexes = table.selectedIndexes()
        if len(indexes) == 0:
            return
        if not self.qSetBusy(True):
            return
        index=indexes[0].row()

        table.clear()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ['formula', 'theoretic mz', 'mz', 'ppm', 'use for calibration'])
        massCali = list(workspace.fileCalibrations.values())[0] if len(workspace.fileCalibrations) == 1 else \
             workspace.fileCalibrations[workspace.showedAveragedSpectra1.filepathTimeSorted[index]]
        ionList = workspace.calibrationIonList

        table.setRowCount(len(ionList))
        for i in range(len(ionList)):
            def setValue(column, s):
                table.setItem(i,column,QtWidgets.QTableWidgetItem(str(s)))
            setValue(0,ionList[i][0])
            setValue(1, massCali.ionsMz[i, 1])
            setValue(2, massCali.ionsMz[i, 0])
            setValue(3, massCali.ionsPpm[i])
            setValue(4,'True' if i in massCali.minIndex else 'False')

        r = (50, 1000)
        X = np.linspace(*r, 1000)
        XX = massCali.func.predictPpm(X) * 1e6
        ax = self.calibrationAx
        ax.clear()

        ax.axhline(color='black',linewidth=0.5)
        ax.plot(X, XX)
        
        ionsMz = massCali.ionsMz
        ionsPpm = massCali.ionsPpm
        minIndex = massCali.minIndex
        maxIndex = massCali.maxIndex
        x = ionsMz[minIndex, 0]
        y = ionsPpm[minIndex]*1e6
        ax.scatter(x,y,c='black')
        x = ionsMz[maxIndex, 0]
        y = ionsPpm[maxIndex]*1e6
        ax.scatter(x, y, c='red')
        
        ax.set_ylabel('ppm')

        self.qSetBusy(False)

    def qCalibrationShowAll(self):
        if not self.qSetBusy(True):
            return
        self.qShowCalibrationAll()
        self.qSetBusy(False)

    def qCalibrationFinish(self):
        pass
