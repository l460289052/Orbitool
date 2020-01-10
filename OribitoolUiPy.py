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


import OribitoolOptions
import OribitoolWorkspace
import OribitoolFormula
import OribitoolFunc

import OribitoolUi
import OribitoolClass


class QThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(OribitoolClass.File, str, int, int)

    def __init__(self, func, args: tuple):
        super(QtCore.QThread, self).__init__(None)
        self.func = func
        self.args = args

    def run(self):
        result = self.func(*self.args, self.sendStatusFunc)
        self.finished.emit((result, self.args))

    def sendStatusFunc(self, file, msg, index, length):
        self.sendStatus.emit(file, msg, index, length)


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
        self.fitPeakPushButton.clicked.connect(self.qfitPeakUseCurrentSpectrum)
        self.peakFitCancelPushButton.clicked.connect(self.qPeakFitRmCancel)

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

        self.peakFitWidget.setLayout(QtWidgets.QVBoxLayout())
        self.peakFitCanvas: matplotlib.backend_bases.FigureCanvasBase = FigureCanvas(
            matplotlib.figure.Figure(figsize=(20, 20)))
        self.peakFitWidget.layout().addWidget(self.peakFitCanvas)
        self.peakFitAx: matplotlib.axes.Axes = self.peakFitCanvas.figure.subplots()
        self.peakFitAx.autoscale(True)
        self.peakFitCanvas.mpl_connect(
            'button_press_event', self.qPeakFitMouseToggle)
        self.peakFitCanvas.mpl_connect(
            'button_release_event', self.qPeakFitMouseToggle)
        self.peakFitCanvas.mpl_connect(
            'motion_notify_event', self.qPeakFitMouseMove)
        self.peakFitNormLine:matplotlib.lines.Line2D=None
        self.peakFitMouseStartPoint = None
        self.peakFitMouseLine: matplotlib.lines.Line2D = None


        self.tabWidget.setCurrentIndex(0)

        self.workspace = OribitoolClass.Workspace()

        self.threads = []
        self.windows = []

        self.busy = False

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
            QtWidgets.QMessageBox.information(
                None, 'busy', "wait for processing")
            return False
        self.busy = busy
        self.widget.setDisabled(busy)
        self.progressBar.setHidden(not busy)
        return True

    def qShowStatus(self, file: OribitoolClass.File, msg: str, current: int, total: int):
        showedMsg = None
        if current >= 0:
            showedMsg = file.name + '\t\t|\t' + msg + '\t|\t\t' + str(current)
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
        fh: OribitoolClass.FileHeader = self.workspace.files.filedict[f].header
        setValue(1, date2str(fh.creationDate + fh.startTime))
        setValue(2, date2str(fh.creationDate + fh.endTime))
        setValue(3, f)

    def qShowFileTimeRange(self):
        timeRange = self.workspace.files.timeRange()
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
            files = self.workspace.addFileFromFolder(
                folder, self.recurrenceCheckBox.isChecked())
            count = table.rowCount()
            table.setRowCount(count+len(files))
            for index, f in enumerate(files):
                self.qShowFile(f, count+index)

        except ValueError as e:
            QtWidgets.QMessageBox.information(
                None, 'Error', 'file "%s" and "%s" have crossed scan time' % (e.args[0], e.args[1]))
            self.workspace.files.clear()
            table.clearContents()
            table.setRowCount(0)

        except:
            pass

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
                if self.workspace.files.addFile(f):
                    addedFiles.append(f)

            table = self.fileTableWidget
            count = table.rowCount()
            table.setRowCount(count+len(addedFiles))
            for index, f in enumerate(addedFiles):
                self.qShowFile(f, count+index)

        except ValueError as e:
            QtWidgets.QMessageBox.information(
                None, 'Error', 'file "%s" and "%s" have crossed scan time' % (e.args[0], e.args[1]))

        self.qShowFileTimeRange()
        self.qSetBusy(False)

    def qRemoveFile(self):
        if not self.qSetBusy(True):
            return
        # indexes = []
        # for srange in self.fileTableWidget.selectedRanges:
        #     for row in range(srange.topRow(), srange.bottomRow()+1):
        #         indexes.append(row)
        # indexes.reverse()
        # for index in indexes:
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
            f: OribitoolClass.File = self.workspace.files.filedict[filepath]
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
            self.workspace.showedSpectra1File = f

            self.tabWidget.setCurrentIndex(1)

        except ValueError as v:
            QtWidgets.QMessageBox.information(None, 'info', str(v))
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

            fileList = workspace.files.subList(
                [table.item(index.row(), 3).text() for index in fileIndexes])

            thread = QThread(OribitoolClass.AveragedSpectra,
                             (fileList, time, N))
            thread.sendStatus.connect(self.qShowStatus)
            thread.finished.connect(self.qAverageFinished)
            self.threads.append(thread)
            thread.start()
        except ValueError as v:
            QtWidgets.QMessageBox.information(None, 'info', str(v))
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
                             (copy.copy(workspace.files), time, N))
            thread.sendStatus.connect(self.qShowStatus)
            thread.finished.connect(self.qAverageFinished)
            self.threads.append(thread)
            thread.start()

        except ValueError as v:
            QtWidgets.QMessageBox.information(None, 'info', str(v))
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

        self.tabWidget.setCurrentIndex(1)

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
            f = workspace.showedSpectra1File
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
            for f in spectrum.files:
                value.append(('files', f.name))
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

    def qfitPeakPlotNormPeakWithoutDraw(self):
        if self.peakFitNormLine is not None:
            self.peakFitNormLine.remove()
            del self.peakFitNormLine
        ax=self.peakFitAx
        normMz = np.linspace(-2e-5, 2e-5, 500)
        peakFitFunc = self.workspace.peakFitFunc
        func = peakFitFunc.func
        if func is None:
            return 
        normIntensity = func.normFunc(normMz)
        lines=ax.plot(normMz, normIntensity, color='black', linewidth=3,
            label="Fit, Res = " + str(int(func.peakResFit)))
        self.peakFitNormLine = lines[-1]
        ax.legend()
        

    def qfitPeakUseCurrentSpectrum(self):
        if not self.qSetBusy(True):
            return
        try:
            workspace = self.workspace
            if workspace.showedSpectra1Type is None:
                raise(ValueError())

            spectrum = workspace.showedSpectrum1
            peakFitFunc = OribitoolClass.PeakFitFunc(spectrum, 100)

            ax = self.peakFitAx
            ax.clear()
            ax.xaxis.set_major_formatter(
                matplotlib.ticker.FormatStrFormatter(r"%.1e"))
            for normPeak in peakFitFunc.normPeaks:
                normPeak: OribitoolClass.Peak
                ax.plot(normPeak.mz, normPeak.intensity)

            self.workspace.peakFitFunc = peakFitFunc
            self.qfitPeakPlotNormPeakWithoutDraw()
           
            self.peakFitCanvas.draw()
            self.tabWidget.setCurrentIndex(2)


        except ValueError as e:
            pass
        self.qSetBusy(False)

    def qPeakFitMouseToggle(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button is matplotlib.backend_bases.MouseButton.LEFT and event.name=='button_press_event':
            self.peakFitMouseStartPoint = (event.xdata, event.ydata)
        elif self.peakFitMouseStartPoint is not None and event.name=='button_release_event':
            workspace = self.workspace
            if workspace.peakFitFunc is not None and event.xdata is not None:
                line = (self.peakFitMouseStartPoint, (event.xdata, event.ydata))
                ax=self.peakFitAx
                func = workspace.peakFitFunc
                peaks=func.normPeaks
                indexes = [index for index in range(len(func.normPeaks)) if OribitoolFunc.linePeakCrossed(line, peaks[index])]
                if len(indexes) == len(peaks):
                    QtWidgets.QMessageBox.information(
                        None,'Error',"couldn't delete all peaks")
                else:
                    indexes.reverse()
                    for index in indexes:
                        func.rm(index) # 相交需要优化...
                        ax.lines.pop(index)
                    self.qfitPeakPlotNormPeakWithoutDraw()
 
                
            
            self.peakFitMouseStartPoint = None
            self.peakFitMouseLine.remove()
            del self.peakFitMouseLine
            self.peakFitMouseLine = None
            self.peakFitCanvas.draw()

    def qPeakFitMouseMove(self, event: matplotlib.backend_bases.MouseEvent):
        if event.button is not matplotlib.backend_bases.MouseButton.LEFT:
            return
        if self.peakFitMouseLine is not None:
            self.peakFitMouseLine.remove()
            del self.peakFitMouseLine
            self.peakFitMouseLine=None

        x1, y1 = self.peakFitMouseStartPoint
        x2 = event.xdata
        y2 = event.ydata
        lines = self.peakFitAx.plot([x1, x2], [y1, y2], color='red')
        self.peakFitMouseLine=lines[-1]
        self.peakFitCanvas.draw()

    def qPeakFitRmCancel(self):
        peak = self.workspace.peakFitFunc.cancel()
        if peak is None:
            return
        ax = self.peakFitAx
        ax.plot(peak.mz, peak.intensity)
        self.qfitPeakPlotNormPeakWithoutDraw()
        self.peakFitCanvas.draw()