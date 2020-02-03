# -*- coding = utf8 -*-
from typing import List, Union, Tuple, Dict
import os
import datetime
import math
from enum import Enum
import copy
import heapq

import scipy.optimize
import numpy as np
from numba import njit
from sortedcontainers import SortedDict

import OribitoolAbstract
import OribitoolFormula
import OribitoolGuessIons
import OribitoolFunc
import OribitoolDll


readFileModule = OribitoolDll


class ShowedSpectraType(Enum):
    File = 0
    Averaged = 1


class Spectrum(OribitoolAbstract.Spectrum):
    def __init__(self, scanNum, mz, intensity):
        self.scanNum = scanNum
        self._mz: np.ndarray = mz
        self._intensity: np.ndarray = intensity


class SpectrumInfo(OribitoolAbstract.SpectrumInfo):
    def __init__(self, info):
        self.info = info

    @property
    def retentionTime(self) -> datetime.timedelta:
        return self.info.retentionTime

    @property
    def scanFilter(self):
        pass

    def getSpectrum(self) -> Spectrum:
        return Spectrum(self.info.scanNum, *self.info.getSpectrum())


class AveragedSpectrum(Spectrum, OribitoolAbstract.AveragedSpectrum):
    def __init__(self, file: OribitoolAbstract.File, timeRange: Tuple[datetime.timedelta, datetime.timedelta] = None, numRange: Tuple[int, int] = None):
        self.fileTime = file.creationDate
        averaged = readFileModule.AveragedSpectrum(
            file._file, timeRange, numRange)

        self._timeRange = averaged.timeRange
        self._numRange = averaged.numRange
        self._mz = averaged.mz
        self._intensity = averaged.intensity


class AveragedSpectra(OribitoolAbstract.AveragedSpectra):
    def __init__(self, fileList, time: datetime.timedelta = None, N: int = None, timeLimit: Tuple[datetime.datetime, datetime.datetime] = None, sendStatus=OribitoolFunc.nullSendStatus):
        if type(fileList) is not FileList:
            raise TypeError()
        fileList: FileList
        timedict=fileList.timedict
        fileTimeSorted = []
        spectra = []
        msg = "average peaks"

        if timeLimit is None:
            timeLimit = fileList.timeRange()
        tmpDelta = datetime.timedelta(seconds=1)
        startTime = timeLimit[0] - tmpDelta
        endTime = timeLimit[1] + tmpDelta
        indexRange = None
        numCount = None
        average = None
        delta = None
        if N is not None:
            def indexRange(f: File):
                retentionStartTime = startTime - f.creationDate
                retentionEndTime = endTime-f.creationDate
                if f.startTime > retentionStartTime and f.endTime < retentionEndTime:
                    return (f.firstScanNumber, f.lastScanNumber + 1)
                if f.creationDate + f.endTime < startTime or f.creationDate+f.startTime > endTime:
                    return (f.lastScanNumber+1, f.lastScanNumber+1)
                else:
                    start = None
                    end = None
                    infoList = f.getSpectrumInfoList()
                    if f.startTime > retentionStartTime:
                        start = f.firstScanNumber
                    else:
                        start = f.firstScanNumber + OribitoolFunc.indexFirstNotSmallerThan(
                            infoList, retentionStartTime, method=(lambda array, index: array[index].retentionTime))
                    if f.endTime < retentionEndTime:
                        end = f.lastScanNumber + 1
                    else:
                        end = f.firstScanNumber+OribitoolFunc.indexFirstBiggerThan(
                            infoList, retentionEndTime, method=(lambda array, index: array[index].retentionTime))
                    return (start, end)

            def numCount(f: File):
                start, end = indexRange(f)
                return math.ceil((end-start+1)/N)

            def average(f: File, left, end):
                right = left + N
                if right > end:
                    right = end
                return AveragedSpectrum(f, numRange=(left, right))
            delta = N

        elif time is not None:
            def indexRange(f: File):
                retentionStartTime = startTime - f.creationDate
                retentionEndTime = endTime-f.creationDate
                if f.startTime > retentionStartTime and f.endTime < retentionEndTime:
                    return (datetime.timedelta(), f.endTime)
                elif f.creationDate + f.endTime < startTime or f.creationDate + f.startTime > endTime:
                    return (f.endTime + tmpDelta, f.endTime + tmpDelta)
                else:
                    start = datetime.timedelta() if f.startTime > retentionStartTime else retentionStartTime
                    end = endTime if f.endTime < retentionEndTime else retentionEndTime
                    return (start, end)

            def numCount(f: File):
                start, end = indexRange(f)
                return math.ceil((end-start)/time)

            def average(f: File, left, end):
                right = left + time
                if right > end:
                    right = end
                return AveragedSpectrum(f, timeRange=(left, right))
            delta = time

        total = sum([numCount(f) for f in fileList.pathdict.values()])

        for f in timedict.values():
            fileTimeSorted.append(f.creationDate)
            index, end = indexRange(f)
            while index < end:
                sendStatus(f.creationDate, msg, len(spectra), total)
                spectra.append(average(f, index, end))
                index += delta

        sendStatus(f.creationDate, msg, len(spectra), len(spectra))

        fileTimeSpectraMap = {}
        for fileTime in fileTimeSorted:
            fileTimeSpectraMap[fileTime] = []
        for spectrum in spectra:
            fileTimeSpectraMap[spectrum.fileTime].append(spectrum)

        self.time = time
        self.N = N
        self.fileTimeSorted = fileTimeSorted
        self.fileTimeSpectraMap = fileTimeSpectraMap
        self.spectra = spectra

    def __len__(self):
        return len(self.spectra)


class File(OribitoolAbstract.File):
    def __init__(self, fullname):
        self.path = fullname
        self.name = os.path.split(fullname)[1]
        self._file = readFileModule.File(fullname)

    def getSpectrumInfo(self, scanNum) -> SpectrumInfo:
        return SpectrumInfo(self._file.getSpectrumInfo(scanNum))

    def getSpectrumInfoList(self) -> List[SpectrumInfo]:
        return [self.getSpectrumInfo(scanNum) for scanNum in range(self.firstScanNumber, self.lastScanNumber+1)]

    @property
    def creationDate(self) -> datetime.datetime:
        return self._file.creationDate

    @property
    def startTime(self) -> datetime.timedelta:
        return self._file.startTime

    @property
    def endTime(self) -> datetime.timedelta:
        return self._file.endTime

    @property
    def firstScanNumber(self) -> int:
        return self._file.firstScanNumber

    @property
    def lastScanNumber(self) -> int:
        return self._file.lastScanNumber


class FileList(object):
    '''
    file list
    '''

    def __init__(self):
        # datetime -> File
        self.timedict = SortedDict()
        self.pathdict: Dict[str, File] = {}

    def crossed(self, start: datetime.datetime, end: datetime.datetime) -> (bool, File):
        timedict=self.timedict
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

    def subList(self, filepaths: List[str]):
        subList = FileList()
        for fpath in filepaths:
            if fpath in self.pathdict:
                subList._addFile(self.pathdict[fpath])
        return subList

    def clear(self):
        self.pathdict.clear()
        self.timedict.clear()

    def timeRange(self):
        timedict=self.timedict
        if len(self.timedict) > 0:
            l: File = timedict.peekitem(0)[1]
            r: File = timedict.peekitem(1)[1]
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


class Peak(OribitoolAbstract.Peak):
    def __init__(self, spectrum: Spectrum, indexRange: range, mz=None, intensity=None):
        '''
        not copy mz
        `subscripts`: (lindex,rindex), both mz[lindex] and mz[rindex] are belong to this peak
        '''
        self._spectrum = spectrum
        self._indexRange = indexRange
        self._mz = mz if mz is not None else spectrum.mz
        self._intensity = intensity if intensity is not None else spectrum.intensity

    @property
    def mz(self) -> np.ndarray:
        return self._mz[self._indexRange]

    @property
    def intensity(self) -> np.ndarray:
        return self._intensity[self._indexRange]

    @property
    def maxIntensity(self):
        if hasattr(self, '_maxIntensity'):
            return getattr(self, '_maxIntensity')
        self._maxIntensity = self.intensity.max()
        return self._maxIntensity

    def peakAt(self) -> np.ndarray:
        '''
        if len(mz)=11,
        len(result)=9
        mz    0  1  2  3  4  3  4  3  2  1  0
        result   F  F  F  T  F  T  F  F  F  
        '''
        if hasattr(self, '_peakAt'):
            return getattr(self, '_peakAt')
        a=self.intensity
        length = len(a)
        a = a[0:length - 1] < a[1:length]
        length = len(a)
        a = a[0:length - 1] > a[1:length]
        self._peakAt = a
        return a

    @property
    def peaksNum(self) -> int:
        if hasattr(self, '_peaksNum'):
            return getattr(self, '_peaksNum')
        self._peaksNum = np.sum(self.peakAt())
        return self._peaksNum


def getPeaks(spectrum: OribitoolAbstract.Spectrum, indexRange: (int, int) = None, mzRange: (float, float) = None):
    peaks = []
    start = None
    stop = None
    if indexRange is not None:
        start, stop = indexRange
    elif mzRange is not None:
        start, stop = OribitoolFunc.indexBetween_njit(spectrum.mz, mzRange)
    else:
        start = 0
        stop = len(spectrum.mz)
    index = 0
    while start < stop:
        rstart, rstop = OribitoolFunc.findPeak(
            spectrum.mz, spectrum.intensity,(start, stop))
        if rstart < stop:
            peaks.append(Peak(spectrum, range(rstart, rstop)))
            index += 1
        start = rstop

    return peaks


class FittedPeak(Peak, OribitoolAbstract.FittedPeak):
    def __init__(self, originalPeak: Peak, fitPeakFunc: OribitoolAbstract.FitPeakFunc, peaksNum, mz=None, fittedParam=None):
        '''
        all fitted peak from the same original peak should have same mz
        '''
        self.originalPeak = originalPeak
        if mz is None:
            mz = originalPeak.mz
        if fittedParam is None:
            fittedParam = fitPeakFunc.getFittedParam(originalPeak)

        delta = 1e-6
        intensity = fitPeakFunc._funcFit(mz, *fittedParam)
        select = intensity > delta
        # stretch
        select[:-1] |= select[1:]
        select[1:] |= select[:-1]

        self._spectrum = originalPeak.spectrum
        self._peaksNum = peaksNum
        self._mz = mz[select]
        self._intensity = intensity[select]
        self._param = fittedParam
        self._peakPosition = fitPeakFunc.getPeakPosition(self)
        self._peakIntensity = fitPeakFunc.getPeakIntensity(self)
        self._area = fitPeakFunc.getArea(self)

    @property
    def mz(self) -> np.ndarray:
        return self._mz

    @property
    def intensity(self) -> np.ndarray:
        return self._intensity

    @property
    def maxIntensity(self):
        return self._peakIntensity

    @property
    def peaksNum(self):
        '''
        return the number of original peak split (not equal to originalpeak's peaksnum)
        '''
        return self._peaksNum


class PeakFitFunc(object):
    def __init__(self, spectrum: OribitoolAbstract.Spectrum, num: int):
        peaks = getPeaks(spectrum)
        peaks = [peak for peak in peaks if peak.peaksNum == 1]
        num = max(0, min(num, len(peaks)))

        peaks = sorted(
            peaks, key=lambda peak: peak.maxIntensity, reverse=True)
        peaks = peaks[0:num]
        Func = OribitoolFunc.NormalDistributionFunc
        params: list = [Func.getParam(peak) for peak in peaks]
        normPeaks: List[Tuple[np.ndarray, np.ndarray]] = [Func.getNormalizedPeak(
            peaks[index], params[index]) for index in range(num)]

        self.Func = Func
        self.peaks = peaks
        self.params = params
        self.normPeaks = normPeaks
        self.canceled: List[List[Tuple[Peak, tuple,
                                       Tuple[np.ndarray, np.ndarray]]]] = []
        self._func = None

    def rm(self, index: Union[int, List]):
        indexes = index if isinstance(index, list) else [index]
        indexes = sorted(copy.copy(indexes), reverse=True)
        removed = []
        for i in indexes:
            peak = self.peaks.pop(i)
            param = self.params.pop(i)
            normPeak = self.normPeaks.pop(i)
            removed.append((peak, param, normPeak))
        self.canceled.append(removed)

        self._func = None

    def cancel(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        if len(self.canceled) == 0:
            return []
        removed = self.canceled.pop()
        normPeaks = []
        for r in removed:
            peak, param, normPeak = r
            self.peaks.append(peak)
            self.params.append(param)
            self.normPeaks.append(normPeak)
            normPeaks.append(normPeak)
        self._func = None
        return normPeaks

    @property
    def func(self) -> OribitoolAbstract.FitPeakFunc:
        if self._func is None and len(self.params) > 0:
            self._func = self.Func(self.params)
        return self._func

    def fitPeak(self, peak: Peak, num: int = None, force:bool=False) -> List[FittedPeak]:
        params = self.func.splitPeakAsParams(peak, num, force)
        peaks = []
        num = len(params)
        for param in params:
            peaks.append(FittedPeak(peak, self.func,
                                    fittedParam=param, peaksNum=num))
        if len(peaks) > 1:
            peaks.sort(key=lambda peak: peak.peakPosition)
        return peaks

    def fitPeaks(self, peaks: List[Peak], sendStatus=OribitoolFunc.nullSendStatus) -> List[FittedPeak]:
        '''
        if peaks are sorted, ret will be sorted be peakPosition
        '''
        fittedPeaks = []
        for peak in peaks:
            fittedPeaks.extend(self.fitPeak(peak))
        return fittedPeaks


class CalibrateMass(object):
    '''
    calibrate for file
    '''

    def __init__(self, fileTime, averagedSpectra: List[OribitoolAbstract.Spectrum], peakFitFunc: PeakFitFunc, ionList: List[OribitoolFormula.Formula], funcArgs, ppm=1, useNIons=None):
        ppm *= 1e-6
        ionsMz = []
        ionsMzTho = np.zeros(len(ionList))
        for index, ion in enumerate(ionList):
            mass = ion.mass()
            ionsMzTho[index] = mass
            maxDelta = 0.1
            mzRange = (mass-maxDelta, mass+maxDelta)

            def process(spectrum: OribitoolAbstract.Spectrum):
                peaks = getPeaks(spectrum, mzRange=mzRange)
                peaks = peakFitFunc.fitPeaks(peaks)
                if len(peaks) == 0:
                    return mass-2*maxDelta
                mz = OribitoolFunc.valueNearest(peaks, mass, method=(
                    lambda peaks, index: peaks[index].peakPosition))
                return mz
            mz = [process(spectrum) for spectrum in averagedSpectra]
            mz = np.array(mz)
            absDeltaPpm = abs(1 - mass / mz)
            sub = absDeltaPpm < ppm
            if np.count_nonzero(sub) > 0:
                mz = mz[sub]
            ionsMz.append(np.average(mz))

        ionsMz = np.array(ionsMz)
        ionsMz = np.stack([ionsMz, ionsMzTho], 1)

        ionsPpm = 1-ionsMz[:, 1]/ionsMz[:, 0]
        length = len(ionsPpm)
        if length < useNIons:
            useNIons = length
        minIndex = heapq.nsmallest(useNIons, range(length), abs(ionsPpm).take)
        maxIndex = heapq.nlargest(
            length-useNIons, range(length), abs(ionsPpm).take)

        Func = OribitoolFunc.PolynomialRegressionFunc
        func = Func(ionsMz[minIndex, 0], ionsPpm[minIndex], *funcArgs)

        self.fileTime = fileTime
        self.ionsMz = ionsMz
        self.ionsPpm = ionsPpm
        self.minIndex = minIndex
        self.maxIndex = maxIndex
        self._Func = Func
        self._func = func

    @property
    def func(self) -> OribitoolAbstract.MassCalibrationFunc:
        return self._func


class CalibratedPeak(Peak, OribitoolAbstract.CalibratedPeak):
    def __init__(self, mz: np.ndarray, intensity: np.ndarray, indexRange: range, originalPeak: Peak):
        self.originalpeak = originalPeak
        self._indexRange = indexRange
        self._mz = mz
        self._intensity = intensity
        self._spectrum = originalPeak.spectrum


class CalibratedSpectrum(OribitoolAbstract.CalibratedSpectrum):
    '''
    before calibrate: split spectrum into peaks
    '''

    def __init__(self, fileTime, originalSpectrum: OribitoolAbstract.Spectrum, timeRange: Tuple[datetime.datetime, datetime.datetime], massCalibrator: CalibrateMass):
        '''
        before calibrate: split spectrum into peaks
        '''
        self._fileTime = fileTime
        self._origin = originalSpectrum

        peaks = getPeaks(originalSpectrum)
        mz = np.concatenate([peak.mz for peak in peaks])
        intensity = np.concatenate([peak.intensity for peak in peaks])
        calibratedPeaks = []
        start = 0

        for peak in peaks:
            stop = start + len(peak.mz)
            calibratedPeak = CalibratedPeak(
                mz, intensity, range(start, stop), peak)
            calibratedPeaks.append(calibratedPeak)
            start = stop
        self._mz = mz
        self._intensity = intensity
        self._peaks = calibratedPeaks
        self._startTime = timeRange[0]
        self._endTime = timeRange[1]
        self.calibrator = massCalibrator
        self.calibrated = False

    @property
    def mz(self):
        if not self.calibrated:
            self._mz = self.calibrator.func.predictMz(self._mz)
            self.calibrated = True
        return self._mz

    @property
    def peaks(self):
        if not self.calibrated:
            self._mz = self.calibrator.func.predictMz(self._mz)
            self.calibrated = True
        return self._peaks

    @property
    def intensity(self):
        return self._intensity


class StandardPeak(OribitoolAbstract.StandardPeak):
    pass


class MassList(OribitoolAbstract.MassList):
    def addPeaks(self, peaks: Union[StandardPeak, List[StandardPeak]]):
        if isinstance(peaks, OribitoolAbstract.StandardPeak):
            peaks = [copy.copy(peaks)]
        else:
            peaks = [copy.copy(peak) for peak in peaks]
        peaks.sort(key=lambda peak: peak.peakPosition)
        for peak in peaks:
            if len(peak.formulaList) == 1:
                peak.peakPosition=peak.formulaList[0].mass()
        peaks1 = self._peaks
        peaks2 = peaks
        iter1 = OribitoolFunc.iterator(peaks1)
        iter2 = OribitoolFunc.iterator(peaks2)
        peaks = []
        ppm = self.ppm
        while not (iter1.end and iter2.end):
            if iter1.end:
                peaks.extend(peaks2[iter2.index:])
                break
            if iter2.end:
                peaks.extend(peaks1[iter1.index:])
                break
            peak1:StandardPeak = iter1.value
            peak2 :StandardPeak= iter2.value
            if abs(peak2.peakPosition / peak1.peakPosition - 1) < ppm:
                if peak1.handled and not peak2.handled:
                    peaks.append(peak1)
                    iter1.next()
                elif not peak1.handled and peak2.handled:
                    peaks.append(peak2)
                    iter2.next()
                else:
                    if peak1.formulaList == peak2.formulaList:
                        peak = StandardPeak((peak1.peakPosition + peak2.peakPosition) / 2,
                                            peak1.formulaList.copy, max(peak1.subpeaks, peak2.subpeaks), not(peak1.isStart or peak2.isStart), peak1.handled)
                        peaks.append(peak)
                    elif peak1.handled and peak2.handled:
                        raise ValueError("can't merge peak in mass list at %.5f with peak at %.5f" % (
                            peak1.peakPosition, peak2.peakPosition))
                    elif len(peak1.formulaList) < len(peak2.formulaList):
                        peaks.append(peak1)
                    elif len(peak1.formulaList) > len(peak2.formulaList):
                        peaks.append(peak2)
                    else:
                        formulaList = list(
                            set(peak1.formulaList) & set(peak2.formulaList))
                        formulaList.sort(key=lambda formula: formula.mass())
                        position = formulaList[0].mass() if len(formulaList) == 1 else(
                            peak1.peakPosition + peak2.peakPosition) / 2
                        peak = StandardPeak(position, formulaList, max(
                            peak1.subpeaks, peak2.subpeaks), not(peak1.isStart or peak2.isStart))
                        peaks.append(peak)
                    iter1.next()
                    iter2.next()
            elif peak1.peakPosition < peak2.peakPosition:
                peaks.append(peak1)
                iter1.next()
            else:
                peaks.append(peak2)
                iter2.next()
        self._peaks = peaks

    def fit(self, spectrum: CalibratedSpectrum, peakFitFunc: PeakFitFunc, ppm=1e-6, sendStatus=OribitoolFunc.nullSendStatus) -> List[Tuple[FittedPeak,StandardPeak]]:
        '''
        len(ret)==len(massList)
        '''
        peaks = spectrum.peaks
        fileTime=spectrum.fileTime
        lsIndex = 0
        lIndex = 0
        length = len(peaks)
        sLength = len(self)
        minRatio = 1 - ppm
        maxRatio = 1 + ppm

        msg = 'fit using mass list'

        fittedPeaks=[]
        while lsIndex < sLength:
            rsIndex = lsIndex + 1
            sendStatus(fileTime,msg,lsIndex,sLength)
            lIndex = OribitoolFunc.indexFirstNotSmallerThan(peaks, self[lsIndex].peakPosition * minRatio, (lIndex, length), (lambda peaks, index: peaks[index].mz.max()))
            rIndex = None
            while True:
                rIndex = OribitoolFunc.indexFirstBiggerThan(peaks, self[rsIndex-1].peakPosition * maxRatio, (lIndex, length), (lambda peaks, index: peaks[index].mz.min()))
                tmp = OribitoolFunc.indexFirstBiggerThan(self, peaks[rIndex-1].mz.max() * maxRatio, (rsIndex, sLength), (lambda speaks, index: speaks[index].peakPosition))
                if tmp == rsIndex:
                    break
                rsIndex = tmp
            fpeaks = peakFitFunc.fitPeaks(peaks[lIndex:rIndex])
            fittedPeaks.extend(OribitoolFunc.standardPeakFittedPeakSimpleMatch(self, fpeaks, ppm, srange=range(lsIndex, rsIndex)))
            lsIndex = rsIndex
        
        sendStatus(fileTime,msg,sLength,sLength)
        return fittedPeaks



class Workspace(object):
    def __init__(self):
        # @showFormulaOption
        self.ionCalculator = OribitoolGuessIons.IonCalculator()

        # only differ in this step
        self.showedSpectra1Type: ShowedSpectraType = None
        # @showFileSpectra1
        self.showedSpectra1FileTime = None
        # @showAveragedSpectra1
        self.showedAveragedSpectra1: AveragedSpectra = None

        # @showSpectrum1
        self.showedSpectrum1: OribitoolAbstract.Spectrum = None

        # @showPeakFitFunc
        self.peakFitFunc: PeakFitFunc = None
        # @showCalibrationIon
        self.calibrationIonList: List[(str, OribitoolFormula.Formula)] = []
        # fileTime ->
        # HNO3NO3-,C6H3O2NNO3-,C6H5O3NNO3-,C6H4O5N2NO3-,C8H12O10N2NO3-,C10H17O10N3NO3-
        self.fileTimeCalibrations: Dict[datetime.datetime, CalibrateMass] = {}
        # @showSpectra2
        self.calibratedSpectra2: List[CalibratedSpectrum] = None
        self.showedSpectrum2Index: int = None
        # @showSpectra2Peaks
        self.showedSpectrum2Peaks: List[Tuple[FittedPeak, StandardPeak]] = None

        # @showSpectra2Peak
        self.showedSpectrum2PeakRange: range = None
        self.showedSpectrum2Peak: List[Tuple[FittedPeak, StandardPeak]] = None

        # @showMassList
        self.massList: MassList = None
