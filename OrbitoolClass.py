# -*- coding: utf-8 -*-
from typing import List, Union, Tuple, Dict
import os
import datetime
import math
from enum import Enum
import copy
import heapq
import multiprocessing

import scipy.optimize
import numpy as np
from numba import njit
from sortedcontainers import SortedDict

import OrbitoolBase
import OrbitoolFormula
import OrbitoolFunc
from OrbitoolDll import File


class FileList(object):
    '''
    file list
    '''

    def __init__(self):
        # datetime -> File
        self.timedict = SortedDict()
        self.pathdict: Dict[str, File] = {}

    def crossed(self, start: datetime.datetime, end: datetime.datetime) -> (bool, File):
        timedict = self.timedict
        index = timedict.bisect_left(start)
        if index > 0:
            k, v = timedict.peekitem(index - 1)
            if v.creationDate + v.endTime > start:
                return (True, v)
        if index < len(timedict):
            k, v = timedict.peekitem(index)
            if k < end:
                return (True, v)
        return (False, None)

    def addFile(self, filepath) -> bool:
        '''
        if add same file with file in timedict, return false
        if added file have crossed time range with file in timedict, raise ValueError
        else return True
        '''
        if filepath in self.pathdict:
            return False
        f = File(filepath)
        crossed, crossedFile = self.crossed(
            f.creationDate + f.startTime, f.creationDate + f.endTime)
        if crossed:
            raise ValueError('file "%s" and "%s" have crossed scan time' % (
                filepath, crossedFile.path))

        self.timedict[f.creationDate] = f
        self.pathdict[f.path] = f
        return True

    def _addFile(self, f: File) -> bool:
        if f.path in self.pathdict:
            return False
        crossed, crossedFile = self.crossed(
            f.creationDate+f.startTime, f.creationDate+f.endTime)
        if crossed:
            raise ValueError(f.path, crossedFile.path)
        self.timedict[f.creationDate] = f
        self.pathdict[f.path] = f
        return True

    def addFileFromFolder(self, folder, recurrent, ext) -> List[datetime.datetime]:
        fileTimes = []
        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() == ext:
                fullname = os.path.join(folder, f)
                if self.addFile(fullname):
                    time = self.pathdict[fullname].creationDate
                    fileTimes.append(time)

        if recurrent:
            for f in os.listdir(folder):
                if os.path.isdir(os.path.join(folder, f)):
                    fileTimes.extend(self.addFileFromFolder(
                        os.path.join(folder, f), recurrent, ext))

        return fileTimes

    def rmFile(self, filepath):
        f: File = self.pathdict.pop(filepath, None)
        if f == None:
            return
        self.timedict.pop(f.creationDate)

    def subList(self, filepathsOrTime: List[Union[str, datetime.datetime]]):
        subList = FileList()
        for pot in filepathsOrTime:
            if isinstance(pot, str):
                if pot in self.pathdict:
                    subList._addFile(self.pathdict[pot])
            elif isinstance(pot, datetime.datetime):
                if pot in self.timedict:
                    subList._addFile(self.pathdict[pot])
        return subList

    def clear(self):
        self.pathdict.clear()
        self.timedict.clear()

    def timeRange(self):
        timedict = self.timedict
        if len(self.timedict) > 0:
            l: File = timedict.peekitem(0)[1]
            r: File = timedict.peekitem(-1)[1]
            return (l.creationDate + l.startTime, r.creationDate + r.endTime)
        else:
            return None

    def __getitem__(self, timeOrPath: Union[datetime.datetime, str]):
        if isinstance(timeOrPath, datetime.datetime):
            return self.timedict[timeOrPath]
        elif isinstance(timeOrPath, str):
            return self.pathdict[timeOrPath]
        else:
            raise TypeError(timeOrPath)

    def __contains__(self, timeOrPath: Union[datetime.datetime, str]):
        if isinstance(timeOrPath, datetime.datetime):
            return timeOrPath in self.timedict
        elif isinstance(timeOrPath, str):
            return timeOrPath in self.pathdict
        else:
            raise TypeError(timeOrPath)


class GetSpectrum(OrbitoolBase.Operator):
    def __init__(self, file: File, ppm: float, numRange: (int, int) = None, timeRange: (datetime.timedelta, datetime.timedelta) = None, polarity=-1):
        self.fileTime = file.creationDate
        self.ppm = ppm
        self.numRange = numRange
        self.timeRange = timeRange
        t1 = None
        t2 = None
        if timeRange is None:
            t1 = file.creationDate + file.getSpectrumRetentionTime(numRange[0])
            t2 = file.creationDate + \
                file.getSpectrumRetentionTime(numRange[1]-1)
        else:
            t1, t2 = timeRange
            t1 += file.creationDate
            t2 += file.creationDate
        self.shownTime = (t1.replace(microsecond=0).isoformat(),
                          t2.replace(microsecond=0).isoformat())
        self.polarity = polarity

        if numRange is None or numRange[1] - numRange[0] > 1:
            self.empty = file.checkAverageEmpty(
                self.timeRange, numRange, self.polarity)
        else:
            self.empty = False

    def __call__(self, fileList: FileList, sendStatus=OrbitoolBase.nullSendStatus):
        fileTime = self.fileTime
        file: File = fileList.timedict[fileTime]
        msg = "averaging"
        sendStatus(fileTime, msg, -1, 0)
        numRange = self.numRange
        if numRange is None or numRange[1] - numRange[0] > 1:
            ret = file.getAveragedSpectrum(
                self.ppm, self.timeRange, numRange, self.polarity)
        else:
            ret = file.getSpectrum(numRange[0])
        return ret


class GetAveragedSpectrumAcrossFiles(OrbitoolBase.Operator):
    def __init__(self, fileList: FileList, spectra: List[GetSpectrum], time, N, now=None):
        self.spectra = spectra

        if N is not None:
            maximum = spectra[0].numRange[1] - spectra[0].numRange[0]
            self.opIndex = 0
            for index, op in enumerate(spectra):
                if op.numRange[1] - op.numRange[0] > maximum:
                    maximum = op.numRange[1] - op.numRange[0]
                    self.opIndex = index

            op = spectra[0]
            file: File = fileList.timedict[op.fileTime]
            s = file.creationDate + \
                file.getSpectrumRetentionTime(op.numRange[0])
            op = spectra[-1]
            file: File = fileList.timedict[op.fileTime]
            t = file.creationDate + \
                file.getSpectrumRetentionTime(op.numRange[1] - 1)
        else:
            maximum = spectra[0].timeRange[1] - spectra[0].timeRange[0]
            self.opIndex = 0
            for index, op in enumerate(spectra):
                if op.timeRange[1] - op.timeRange[0] > maximum:
                    maximum = op.timeRange[1] - op.timeRange[0]
                    self.opIndex = index

            s = now
            t = now + time
        op = spectra[self.opIndex]
        self.fileTime = op.fileTime
        self.ppm = op.ppm
        self.numRange = op.numRange
        self.timeRange = op.timeRange
        self.shownTime = (s.replace(microsecond=0).isoformat(),
                          t.replace(microsecond=0).isoformat())
        self.polarity = spectra[0].polarity
        self.empty = op.empty

    def __call__(self, fileList: FileList, sendStatus=OrbitoolBase.nullSendStatus):
        return self.spectra[self.opIndex](fileList, sendStatus)


def AverageFileList(fileList: FileList, ppm, time: datetime.timedelta = None, N: int = None, polarity: int = -1, timeLimit: Tuple[datetime.datetime, datetime.datetime] = None) -> List[GetSpectrum]:
    timedict = fileList.timedict
    for file in timedict.values():
        if file.getFilter(polarity) is None:
            raise ValueError(
                f"Please check file {file.name}. It doesn't have spectrum with polarity = {polarity}")

    averageSpectra = []

    if timeLimit is None:
        timeLimit = fileList.timeRange()
    tmpDelta = datetime.timedelta(seconds=1)
    startTime = timeLimit[0] - tmpDelta
    endTime = timeLimit[1] + tmpDelta

    if N is not None:
        zero = 0

        def indexRange(f: File):
            retentionStartTime = startTime - f.creationDate
            retentionEndTime = endTime - f.creationDate
            return f.timeRange2NumRange((retentionStartTime, retentionEndTime))

        def average(f: File, left, length):
            right = left + length
            return GetSpectrum(f, ppm, numRange=(left, right), polarity=polarity)

        it = OrbitoolBase.iterator(fileList.timedict.values())
        if it.end:
            return averageSpectra
        nowfile = it.value
        index, stop = indexRange(nowfile)
        while not it.end:
            while index + N <= stop:
                averageSpectra.append(average(nowfile, index, N))
                index += N

            if index == stop:
                it.next()
                if it.end:
                    break
                nowfile = it.value
                index, stop = indexRange(nowfile)
                continue

            spectra = []
            left = N
            while left > zero:
                if left <= stop - index:
                    spectra.append(average(nowfile, index, left))
                    index += left
                    left = zero
                else:
                    count = stop - index
                    spectra.append(average(nowfile, index, count))
                    left -= count
                    it.next()
                    if it.end:
                        break
                    nowfile = it.value
                    index, stop = indexRange(nowfile)
            averageSpectra.append(
                GetAveragedSpectrumAcrossFiles(fileList, spectra, time, N))
        if N == 1:
            averageSpectra = [spectrum for spectrum in averageSpectra if timedict[spectrum.fileTime].getSpectrumPolarity(
                spectrum.numRange[0]) == polarity]

    elif time is not None:
        zero = datetime.timedelta()

        def average(f: File, now, nowend):
            left = now - f.creationDate
            right = nowend - f.creationDate
            return GetSpectrum(f, ppm, timeRange=(left, right), polarity=polarity)

        it = OrbitoolBase.iterator(fileList.timedict.values())
        now = startTime
        nowfile = it.value
        while not it.end and nowfile.creationDate + nowfile.endTime < now:
            it.next()
            nowfile = it.value
        if it.end:
            return averageSpectra

        nowend = now + time
        if nowend > endTime:
            nowend = endTime
        nowfstart = nowfile.creationDate + nowfile.startTime
        nowfend = nowfile.creationDate + nowfile.endTime

        while now <= endTime and not it.end:
            if nowfend >= nowend:
                if nowfstart > nowend:
                    times = int((nowfile.creationDate - now)/time)
                    now += times * time
                    nowend = now + time
                    if now > endTime:
                        break
                    if nowend > endTime:
                        nowend = endTime
                averageSpectra.append(average(nowfile, now, nowend))
                if nowfend == nowend:
                    it.next()
                    nowfile = it.value
                    nowfstart = nowfile.creationDate + nowfile.startTime
                    nowfend = nowfile.creationDate + nowfile.endTime
            else:
                tmpnow = now
                spectra = []
                while True:
                    if nowfend < nowend:
                        spectra.append(average(nowfile, tmpnow, nowfend))
                        tmpnow = nowfend
                        it.next()
                        if it.end:
                            break
                        nowfile = it.value
                        nowfstart = nowfile.creationDate + nowfile.startTime
                        nowfend = nowfile.creationDate + nowfile.endTime
                    else:
                        if nowfstart < nowend:
                            spectra.append(average(nowfile, tmpnow, nowend))
                        break
                averageSpectra.append(GetAveragedSpectrumAcrossFiles(
                    fileList, spectra, time, N, now))

            now += time
            nowend = now + time
            if nowend > endTime:
                nowend = endTime

    averageSpectra = [
        spectra for spectra in averageSpectra if not spectra.empty]
    return averageSpectra


class PeakFitFunc:
    def __init__(self, spectrum: OrbitoolBase.Spectrum, num: int):
        peaks = spectrum.peaks if spectrum.peaks is not None else OrbitoolFunc.getPeaks(
            spectrum)
        peaks = [peak for peak in peaks if peak.splitNum == 1]
        num = max(0, min(num, len(peaks)))

        peaks = sorted(
            peaks, key=lambda peak: peak.maxIntensity, reverse=True)
        peaks = peaks[0:num]
        Func = OrbitoolFunc.NormalDistributionFunc
        normPeaks: List[OrbitoolBase.Peak] = [Func.getNormalizedPeak(
            peak, Func.getParam(peak)) for peak in peaks]

        self.Func = Func
        self.normPeaks = normPeaks
        self.canceled: List[List[OrbitoolBase.Peak]] = []
        self._func = None

    def rm(self, index: Union[int, List]):
        indexes = index if isinstance(index, list) else [index]
        indexes = sorted(copy.copy(indexes), reverse=True)
        removed = []
        for i in indexes:
            normPeak = self.normPeaks.pop(i)
            removed.append(normPeak)
        self.canceled.append(removed)

        self._func = None

    def cancel(self) -> List[OrbitoolBase.Peak]:
        if len(self.canceled) == 0:
            return []
        removed = self.canceled.pop()
        normPeaks = []
        for normPeak in removed:
            self.normPeaks.append(normPeak)
            normPeaks.append(normPeak)
        self._func = None
        return normPeaks

    @property
    def func(self) -> OrbitoolFunc.NormalDistributionFunc:
        if self._func is None and len(self.normPeaks) > 0:
            self._func = self.Func(
                [peak.fittedParam for peak in self.normPeaks])
        return self._func

    def fitPeak(self, peak: OrbitoolBase.Peak, num: int = None, force: bool = False) -> List[OrbitoolBase.Peak]:
        return self.func.splitPeak(peak, num, force)

    def fitPeaks(self, peaks: List[OrbitoolBase.Peak], fileTime: datetime.datetime = datetime.datetime.now(), sendStatus=OrbitoolFunc.nullSendStatus) -> List[OrbitoolBase.Peak]:
        '''
        if peaks are sorted, ret will be sorted be peakPosition
        '''
        fittedPeaks = []
        msg = "fit peaks"
        length = len(peaks)
        for index, peak in enumerate(peaks):
            sendStatus(fileTime, msg, index, length)
            fittedPeaks.extend(self.fitPeak(peak))
        return fittedPeaks


class CalibrateMass:
    '''
    calibrate for file
    '''

    def __init__(self, fileTime, averagedSpectra: List[OrbitoolBase.Spectrum], peakFitFunc: PeakFitFunc, ionList: List[OrbitoolFormula.FormulaHint], funcArgs, ppm=5e-6, useNIons=None):
        ionsMz = []
        ionsMzTho = np.zeros(len(ionList))
        ionsPositions = []
        ionsIntensities = []
        for index, ion in enumerate(ionList):
            mass = ion.mass()
            ionsMzTho[index] = mass
            maxDelta = 0.1
            mzRange = (mass-maxDelta, mass+maxDelta)

            def process(spectrum: OrbitoolBase.Spectrum):
                r = OrbitoolFunc.indexBetween(spectrum.peaks, mzRange, method=(
                    lambda peaks, index: peaks[index].mz.min()))
                peaks = spectrum.peaks[r.start:r.stop]
                peaks = peakFitFunc.fitPeaks(peaks)
                if len(peaks) == 0:
                    return 0, 0
                index = OrbitoolFunc.indexNearest(peaks, mass, method=(
                    lambda peaks, index: peaks[index].peakPosition))
                mz = peaks[index].peakPosition
                intensity = peaks[index].peakIntensity
                return mz, intensity
            rets = [process(spectrum) for spectrum in averagedSpectra]
            rets = np.array(rets, dtype=np.float)
            mz = rets[:, 0]
            ionsPositions.append(mz)
            ionsIntensities.append(rets[:, 1])
            absDeltaPpm = abs(1 - mass / mz)
            sub = absDeltaPpm < ppm
            if np.count_nonzero(sub) > 0:
                mz = mz[sub]
            ionsMz.append(np.average(mz))

        ionsPositions = np.stack(ionsPositions, 1)
        ionsIntensities = np.stack(ionsIntensities, 1)

        ionsMz = np.array(ionsMz, dtype=np.float)
        ionsMz = np.stack([ionsMz, ionsMzTho], 1)

        ionsPpm = 1-ionsMz[:, 1]/ionsMz[:, 0]
        length = len(ionsPpm)
        if length < useNIons:
            useNIons = length
        minIndex = heapq.nsmallest(useNIons, range(length), abs(ionsPpm).take)
        maxIndex = heapq.nlargest(
            length-useNIons, range(length), abs(ionsPpm).take)

        Func = OrbitoolFunc.PolynomialRegressionFunc
        func = Func(ionsMz[minIndex, 0], ionsPpm[minIndex], *funcArgs)

        self.fileTime = fileTime
        # ionsPositions[i,j] -> i-th spectrum, j-th ions
        self.ionsPositions = ionsPositions
        self.ionsIntensities = ionsIntensities

        self.ionsMz = ionsMz
        self.ionsPpm = ionsPpm
        self.minIndex = minIndex
        self.maxIndex = maxIndex
        self.Func = Func
        self.func = func

    def fitSpectrum(self, spectrum: OrbitoolBase.Spectrum) -> OrbitoolBase.Spectrum:
        newSpectrum = copy.copy(spectrum)
        peaks = newSpectrum.peaks
        newSpectrum.mz = self.func.predictMz(
            np.concatenate([peak.mz for peak in peaks]))
        newSpectrum.intensity = np.concatenate(
            [peak.intensity for peak in peaks])
        newPeaks = []
        start = 0
        for peak in newSpectrum.peaks:
            stop = start + len(peak.mz)
            newPeak: OrbitoolBase.Peak = peak.copy(
                newSpectrum, range(start, stop))
            newPeaks.append(newPeak)
            start = stop
        newSpectrum.peaks = newPeaks
        return newSpectrum

    @staticmethod
    def fitSpectra(fileTime: datetime.datetime, massCalibrate, spectra: List[OrbitoolBase.Spectrum]) -> List[OrbitoolBase.Spectrum]:
        return [massCalibrate.fitSpectrum(spectrum) for spectrum in spectra]


def fitUseMassList(massList: OrbitoolBase.MassList, spectrum: OrbitoolBase.Spectrum, peakFitFunc: PeakFitFunc, sendStatus=OrbitoolBase.nullSendStatus):
    '''
    len(ret)==len(massList)
    '''
    peaks = spectrum.peaks
    fileTime = spectrum.fileTime

    ppm = massList.ppm
    minRatio = 1 - ppm
    maxRatio = 1 + ppm

    select = np.zeros(len(peaks), dtype=np.bool)
    length = len(massList)
    msg = 'parting using mass list'
    for index, peak in enumerate(massList):
        sendStatus(fileTime, msg, index, length)
        l = OrbitoolFunc.indexFirstNotSmallerThan(
            peaks, peak.peakPosition * minRatio, method=(lambda peaks, index: peaks[index].mz[-1]))
        r = OrbitoolFunc.indexFirstBiggerThan(
            peaks, peak.peakPosition*maxRatio, method=(lambda peaks, index: peaks[index].mz[0]))
        select[l:r] = True

    peaks = [peak for peak, slt in zip(peaks, select) if slt]

    fittedPeaks = peakFitFunc.fitPeaks(peaks, fileTime, sendStatus)

    msg = 'matching with mass list'
    length = len(massList)
    flIndex = 0
    fLength = len(fittedPeaks)
    for index, peak in enumerate(massList):
        sendStatus(fileTime, msg, index, length)
        frIndex = OrbitoolFunc.indexNearest(fittedPeaks, peak.peakPosition, (
            flIndex, fLength), method=(lambda peaks, index: peaks[index].peakPosition))
        if frIndex < 0 or frIndex >= fLength:
            break
        fpeak = fittedPeaks[frIndex]
        if abs(fpeak.peakPosition / peak.peakPosition - 1) < ppm:
            fpeak.addFormula(peak.formulaList)
        flIndex = frIndex

    for fpeak in fittedPeaks:
        if not hasattr(fpeak, 'formulaList'):
            fpeak.addFormula([])
    sendStatus(fileTime, msg, length, length)

    return fittedPeaks, OrbitoolFunc.calculateResidual(fittedPeaks, peakFitFunc.func, spectrum.fileTime, sendStatus)


def getTimeSeries(mz: float, ppm: float, calibratedSpectra: List[OrbitoolBase.Spectrum], peakFitFunc: PeakFitFunc, tag: str, sendStatus=OrbitoolFunc.nullSendStatus):
    '''
    @mz:
    @ppm: example 1e-6
    '''
    time = []
    fmz = []
    intensity = []
    minmz = mz * (1 - ppm)
    maxmz = mz * (1 + ppm)

    length = len(calibratedSpectra)
    msg = "calc peak at %f" % mz
    for index, calibratedSpectrum in enumerate(calibratedSpectra):
        sendStatus(calibratedSpectrum.fileTime, msg, index, length)

        peaks = calibratedSpectrum.peaks
        lIndex = OrbitoolFunc.indexFirstNotSmallerThan(
            peaks, minmz, method=(lambda peaks, i: peaks[i].mz.max()))
        rIndex = OrbitoolFunc.indexFirstBiggerThan(
            peaks, maxmz, method=(lambda peaks, i: peaks[i].mz.min()))
        peaks = peakFitFunc.fitPeaks(peaks[lIndex:rIndex])
        if len(peaks) > 0:
            i = 0 if len(peaks) == 1 else OrbitoolFunc.indexNearest(
                peaks, mz, method=(lambda peaks, i: peaks[i].peakPosition))
            peak: FittedPeak = peaks[i]
            if peak.peakPosition > minmz and peak.peakPosition < maxmz:
                time.append(calibratedSpectrum.timeRange[0])  # use start time
                fmz.append(peak.peakPosition)
                intensity.append(peak.peakIntensity)
    time = np.array(time, dtype=np.datetime64)
    fmz = np.array(fmz, dtype=np.float)
    intensity = np.array(intensity, dtype=np.float)

    sendStatus(calibratedSpectrum.fileTime, msg, index, length)

    return OrbitoolBase.TimeSeries(time, intensity, mz, ppm, tag)


supportedVersion = 1_02_00
version = 1_02_09


def version2Str(version):
    v1 = int(version / 10000)
    version -= v1*10000
    v2 = int(version / 100)
    version -= v2 * 100
    v3 = version
    return f"{v1}.{v2}.{v3}"


class Workspace(object):
    def __init__(self):
        self.version = version
        # @showSpectra
        self.spectra1Operators: List[Union[GetSpectrum,
                                           GetSpectrum]] = None
        # @showSpectrum1
        self.spectrum1: OrbitoolBase.Spectrum = None
        self.noise: (np.ndarray, np.ndarray) = None
        self.LOD: (float, float) = None
        self.denoisedSpectrum1: OrbitoolBase.Spectrum = None

        # @showPeakFit2Spectra
        self.spectra2LODs: List[(float, float)] = None
        self.denoisedSpectra2: List[OrbitoolBase.Spectrum] = None
        # datetime.datetime, List[Spectrum]
        self.fileTimeSpectraMaps: SortedDict = None

        # @showPeakFitFunc
        self.peakFitFunc: PeakFitFunc = None
        # @showCalibrationInfoAll
        # datetime.datetime, CalibrateMass
        # HNO3NO3-,C6H3O2NNO3-,C6H5O3NNO3-,C6H4O5N2NO3-,C8H12O10N2NO3-,C10H17O10N3NO3-
        self.fileTimeCalibrations: SortedDict = None

        self.calibratedSpectra3: List[OrbitoolBase.Spectrum] = None
        self.shownSpectrum3Index: int = None
        # @showSpectrum3Peaks
        self.spectrum3fittedPeaks = None
        self.spectrum3Residual: (np.ndarray, np.ndarray) = None

        # @showSpectrum3Peak
        self.shownSpectrum3PeakRange: range = None
        self.shownSpectrum3Peak: List[OrbitoolBase.Peak] = None

        # @showMassList
        self.massList: MassList = OrbitoolBase.MassList()

        # @showTimeSerieses
        self.timeSerieses: List[TimeSeries] = []
        self.timeSeriesIndex = None