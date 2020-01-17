from typing import List, Union, Tuple, Dict
import os
import datetime
import gzip
from enum import Enum
import copy
import heapq

import scipy.optimize
import numpy as np
import jsonpickle
from bintrees import FastRBTree

import OribitoolAbstract
import OribitoolFormula
import OribitoolFunc
import OribitoolDll


readFileModule = OribitoolDll


def objToFile(path: str, obj):
    with open(path, 'w') as writer:
        # with gzip.open(path, 'wb') as writer:
        writer.write(jsonpickle.encode(obj))


def objFromFile(path: str):
    with open(path, 'r') as reader:
        # with gzip.open(path, 'rb') as reader:
        return jsonpickle.decode(reader.read())


class ShowedSpectraType(Enum):
    File = 0
    Averaged = 1


class FileHeader(OribitoolAbstract.FileHeader):
    def __init__(self, file: OribitoolAbstract.File):
        self._file = file
        self.header = readFileModule.FileHeader(file._file)

    @property
    def file(self):
        return self._file

    @property
    def creationDate(self) -> datetime.datetime:
        return self.header.creationDate

    @property
    def startTime(self) -> datetime.timedelta:
        return self.header.startTime

    @property
    def endTime(self) -> datetime.timedelta:
        return self.header.endTime

    @property
    def firstScanNumber(self) -> int:
        return self.header.firstScanNumber

    @property
    def lastScanNumber(self) -> int:
        return self.header.lastScanNumber


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


class AveragedSpectrum(OribitoolAbstract.AveragedSpectrum):
    def __init__(self, files: List[OribitoolAbstract.File], timeRanges: List[Tuple[datetime.timedelta, datetime.timedelta]] = None, numRanges: List[Tuple[int, int]] = None):
        self.filepaths = [file.path for file in files]
        averaged = readFileModule.AveragedSpectrum(
            [f._file for f in files], timeRanges, numRanges)

        self._timeRange = averaged._timeRange
        self._num = averaged.num
        self._timeRanges = averaged.timeRanges
        self._numRanges = averaged.numRanges
        self._mz = averaged.mz
        self._intensity = averaged.intensity


class AveragedSpectra(OribitoolAbstract.AveragedSpectra):
    def __init__(self, fileList, time: datetime.timedelta = None, N: int = None, sendStatus=OribitoolFunc.nullSendStatus):
        if type(fileList) is not FileList:
            raise TypeError()
        fileList: FileList
        tree = fileList.filetree
        filepathTimeSorted = []
        spectra = []
        msg = "average peaks"
        total = None
        if N is not None:
            total = sum([(f.header.lastScanNumber-f.header.firstScanNumber+1)
                         for f in fileList.filedict.values()])/N+1
            toBeProcessed = None
            numRanges = None
            try:
                k, f = tree.min_item()
                f: File
                h = f.header
                index = h.firstScanNumber
                left = h.lastScanNumber - index + 1
                filepathTimeSorted.append(f.path)
                while True:
                    toBeProcessed = [f]
                    numRanges = []
                    if left < N:
                        numRanges.append((index, h.lastScanNumber))
                        Nleft = N-left
                        while Nleft > 0:
                            k, f = tree.succ_item(k)
                            h = f.header
                            index = h.firstScanNumber
                            left = h.lastScanNumber - index + 1
                            filepathTimeSorted.append(f.path)

                            toBeProcessed.append(f)
                            if left < Nleft:
                                numRanges.append((index, h.lastScanNumber))
                                Nleft -= left
                            elif left == Nleft:
                                numRanges.append((index, h.lastScanNumber))
                                Nleft = 0
                                k, f = tree.succ_item(k)
                                h = f.header
                                index = h.firstScanNumber
                                left = h.lastScanNumber - index + 1
                                filepathTimeSorted.append(f.path)
                            else:  # left > Nleft
                                numRanges.append((index, index + Nleft - 1))
                                index += Nleft
                                left -= Nleft
                                Nleft = 0

                    elif left == N:
                        numRanges.append((index, h.lastScanNumber))
                        k, f = tree.succ_item(k)
                        h = f.header
                        index = h.firstScanNumber
                        left = h.lastScanNumber-index+1
                        filepathTimeSorted.append(f.path)
                    else:  # left > N
                        numRanges.append((index, index+N-1))
                        index += N
                        left -= N

                    sendStatus(f.path, msg, len(spectra), total)
                    spectra.append(AveragedSpectrum(
                        toBeProcessed, numRanges=numRanges))
                    # if want to use multi-process, u can add a process pool
                    # and add this to the pool
            except KeyError:
                sendStatus(f.path, msg, len(spectra), total)
                spectra.append(AveragedSpectrum(
                    toBeProcessed, numRanges=numRanges))
        elif time is not None:
            total = datetime.timedelta()
            for f in fileList.filedict.values():
                total += f.header.endTime
            total = int(total/time)+1
            toBeProcessed = None
            timeRanges = None
            try:
                k, f = tree.min_item()
                f: File
                h = f.header
                now = datetime.timedelta()
                left = h.endTime
                filepathTimeSorted.append(f.path)
                while True:
                    toBeProcessed = [f]
                    timeRanges = []
                    if left < time:
                        timeRanges.append((now, h.endTime))
                        Tleft = time - left
                        while Tleft > datetime.timedelta():
                            k, f = tree.succ_item(k)
                            h = f.header
                            now = datetime.timedelta()
                            left = h.endTime
                            filepathTimeSorted.append(f.path)

                            toBeProcessed.append(f)
                            if left < Tleft:
                                timeRanges.append((now, h.endTime))
                                Tleft -= left
                            else:  # left > Tleft
                                timeRanges.append((now, now + Tleft))
                                now += Tleft
                                left -= Tleft
                                Tleft = datetime.timedelta(minutes=-1)
                    else:  # left > time
                        timeRanges.append((now, now + time))
                        now += time
                        left -= time

                    sendStatus(f.path, msg, len(spectra), total)
                    spectra.append(AveragedSpectrum(
                        toBeProcessed, timeRanges=timeRanges))
            except KeyError:
                sendStatus(f.path, msg, len(spectra), total)
                spectra.append(AveragedSpectrum(
                    toBeProcessed, timeRanges=timeRanges))

        sendStatus(f.path, msg, len(spectra), len(spectra))

        filepathSpectraMap = {}
        for filepath in filepathTimeSorted:
            filepathSpectraMap[filepath] = []
        for spectrum in spectra:
            paths = spectrum.filepaths
            if len(paths) == 1:
                filepathSpectraMap[paths[0]].append(spectrum)

        self.time = time
        self.N = N
        self.filepathTimeSorted = filepathTimeSorted
        self.filepathSpectraMap = filepathSpectraMap
        self.spectra = spectra

    def __len__(self):
        return len(self.spectra)


class File(OribitoolAbstract.File):
    def __init__(self, fullname):
        self.path = fullname
        self.name = os.path.split(fullname)[1]
        self._file = readFileModule.File(fullname)
        self._header = FileHeader(self._file.header)

    @property
    def header(self) -> FileHeader:
        return self._header

    def getSpectrumInfo(self, scanNum) -> SpectrumInfo:
        return SpectrumInfo(self._file.getSpectrumInfo(scanNum))

    def getSpectrumInfoList(self) -> List[SpectrumInfo]:
        h = self.header
        return [self.getSpectrumInfo(scanNum) for scanNum in range(h.firstScanNumber, h.lastScanNumber+1)]


class FileList(object):
    '''
    file header list
    '''

    def __init__(self):
        # sorted by start time
        self.filetree = FastRBTree()
        # path -> File
        self.filedict = {}

    def crossed(self, left: datetime.datetime, right: datetime.datetime) -> (bool, File):
        try:
            k, v = self.filetree.floor_item(left)
            if v.header.creationDate + v.header.endTime > left:
                return (True, v)
        except KeyError:
            pass
        try:
            k, v = self.filetree.ceiling_item(left)
            if k < right:
                return (True, v)
        except KeyError:
            pass
        return (False, None)

    def addFile(self, filePath) -> bool:
        '''
        if add same file with file in filedict, return false
        if added file have crossed time range with file in fiedict, raise ValueError
        else return True
        '''
        if filePath in self.filedict:
            return False
        f = File(filePath)
        h = f.header
        crossed, crossedFile = self.crossed(
            h.creationDate + h.startTime, h.creationDate + h.endTime)
        if crossed:
            raise ValueError(filePath, crossedFile.path)

        self.filetree.insert(h.creationDate + h.startTime, f)
        self.filedict[filePath] = f
        return True

    def _addFile(self, f: File) -> bool:
        if f.path in self.filedict:
            return False
        h = f.header
        crossed, crossedFile = self.crossed(
            h.creationDate+h.startTime, h.creationDate+h.endTime)
        if crossed:
            raise ValueError(f.path, crossedFile.path)
        self.filetree.insert(h.creationDate + h.startTime, f)
        self.filedict[f.path] = f
        return True

    def addFileFromFolder(self, folder, recurrent, ext):
        files = []
        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() == ext:
                fullname = os.path.join(folder, f)
                if self.addFile(fullname):
                    files.append(fullname)

        if recurrent:
            for f in os.listdir(folder):
                if os.path.isdir(os.path.join(folder, f)):
                    files.extend(self.addFileFromFolder(
                        os.path.join(folder, f), recurrent, ext))

        return files

    def rmFile(self, fullFileName):
        f: File = self.filedict.pop(fullFileName, None)
        if f == None:
            return
        self.filetree.remove(f.header.creationDate + f.header.startTime)

    def subList(self, filePaths: List[str]):
        subList = FileList()
        for fpath in filePaths:
            if fpath in self.filedict:
                subList._addFile(self.filedict[fpath])
        return subList

    def averageByNum(self, N: int):
        pass

    def averageByTime(self, time: float):
        '''
        `time`:minutes
        '''
        pass

    def clear(self):
        self.filetree.clear()
        self.filedict.clear()

    def timeRange(self):
        if len(self.filedict) > 0:
            l: File = self.filetree.min_item()[1]
            r: File = self.filetree.max_item()[1]
            l = l.header
            r = r.header
            return (l.creationDate + l.startTime, r.creationDate + r.endTime)
        else:
            return None


class Peak(OribitoolAbstract.Peak):
    def __init__(self, spectrum: Spectrum, subscripts: Tuple[int, int], copyMz=False):
        '''
        `subscripts`: (lindex,rindex), both mz[lindex] and mz[rindex] are belong to this peak
        '''
        self._spectrum = spectrum
        l, r = subscripts
        r += 1
        self._mz: np.ndarray = spectrum.mz[l:r].copy()
        if copyMz:
            self._mz=self._mz.copy()
        self._intensity: np.ndarray = spectrum.intensity[l:r]

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, intensity):
        self._intensity = intensity
        if hasattr(self, '_maxIntensity'):
            delattr(self, '_maxIntensity')

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
        a = self.intensity
        length = len(a)
        a = a[0:length - 1] < a[1:length]
        length = len(a)
        a = a[0:length - 1] > a[1:length]
        self._peakAt = a
        return a

    def peaksNum(self) -> int:
        if hasattr(self, '_peaksNum'):
            return getattr(self, '_peaksNum')
        self._peaksNum = np.sum(self.peakAt())
        return self._peaksNum


def getPeaks(spectrum: OribitoolAbstract.Spectrum, indexRange=None, mzRange=None, copyMz=False):
    peaks = []
    begin = None
    stop = None
    if indexRange is not None:
        begin, stop = indexRange
    elif mzRange is not None:
        r = OribitoolFunc.indexBetween(spectrum.mz, mzRange)
        begin = r.start
        stop = r.stop
    else:
        begin = 0
        stop = len(spectrum.mz)
    index = 0
    while begin < stop:
        l, r = OribitoolFunc.findPeak(
            spectrum.mz, spectrum.intensity, begin, stop)
        if l < stop:
            peaks.append(Peak(spectrum, (l, r), copyMz))
            index += 1
        begin = r

    return peaks


class FittedPeak(OribitoolAbstract.FittedPeak):
    def __init__(self, originalPeak: Peak, fitPeakFunc: OribitoolAbstract.FitPeakFunc, mz=None, fittedParam=None):
        self.originalPeak = originalPeak
        if mz is None:
            mz = originalPeak.mz
        if fittedParam is None:
            fittedParam = fitPeakFunc.getFittedParam(originalPeak)

        delta = 1e-6
        intensity = fitPeakFunc._funcFit(mz, *fittedParam)
        select = intensity > delta
        select[:-1] |= select[1:]
        select[1:] |= select[:-1]

        self._mz = mz[select]
        self._intensity = intensity[select]
        self._param = fittedParam
        self._peakPosition = fitPeakFunc.getPeakPosition(self)
        self._peakIntensity = fitPeakFunc.getPeakIntensity(self)
        self._area = fitPeakFunc.getArea(self)

    @property
    def spectrum(self) -> Spectrum:
        return self.originalPeak.spectrum

    @property
    def maxIntensity(self):
        return self._peakIntensity

    def peakAt(self):
        return Peak.peakAt(self)

    def peaksNum(self):
        return Peak.peaksNum(self)


class PeakFitFunc(object):
    def __init__(self, spectrum: OribitoolAbstract.Spectrum, num: int):
        peaks = getPeaks(spectrum)
        peaks = [peak for peak in peaks if peak.peaksNum() == 1]
        num = max(0, min(num, len(peaks)))

        peaks = sorted(
            peaks, key=lambda peak: peak.maxIntensity, reverse=True)
        peaks = peaks[0:num]
        Func = OribitoolFunc.NormalDistributionFunc
        params: list = [Func.getParam(peak) for peak in peaks]
        normPeaks: List[Peak] = [Func.getNormalizedPeak(
            peaks[index], params[index]) for index in range(num)]

        self.Func = Func
        self.peaks = peaks
        self.params = params
        self.normPeaks = normPeaks
        self.canceled: List[List[Tuple[Peak, tuple, normPeaks]]] = []
        self._func = None

    def rm(self, index: Union[int, List]):
        indexes = index if type(index) is list else [index]
        indexes = sorted(copy.copy(indexes), reverse=True)
        removed = []
        for i in indexes:
            peak = self.peaks.pop(i)
            param = self.params.pop(i)
            normPeak = self.normPeaks.pop(i)
            removed.append((peak, param, normPeak))
        self.canceled.append(removed)

        self._func = None

    def cancel(self) -> List[Peak]:
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

    def fitPeak(self, peak: Peak, num: int = None) -> List[FittedPeak]:
        params = self.func.splitPeakAsParams(peak, num)
        peaks = []
        for param in params:
            peaks.append(FittedPeak(peak, self.func, fittedParam=param))
        if len(peaks) > 1:
            peaks.sort(key=lambda peak: peak.peakPosition)
        return peaks

    def fitPeaks(self, peaks: List[Peak]) -> List[FittedPeak]:
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

    def __init__(self, filepath, averagedSpectra: List[OribitoolAbstract.Spectrum], peakFitFunc: PeakFitFunc, ionList: List[OribitoolFormula.Formula], funcArgs, ppm=1, useNIons=None):
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
                mz = OribitoolFunc.valueFindNearest(peaks, mass, method=(
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

        self.filepath = filepath
        self.ionsMz = ionsMz
        self.ionsPpm = ionsPpm
        self.minIndex = minIndex
        self.maxIndex = maxIndex
        self._Func = Func
        self._func = func

    @property
    def func(self) -> OribitoolAbstract.MassCalibrationFunc:
        return self._func


class CalibratedSpectrum(OribitoolAbstract.CalibratedSpectrum):
    def __init__(self, originalSpectrum: OribitoolAbstract.Spectrum, timeRange: Tuple[datetime.datetime, datetime.datetime], massCalibrator: CalibrateMass):
        self._origin = originalSpectrum
        self._peaks = getPeaks(originalSpectrum, copyMz=True)
        self._mz = np.concatenate([peak.mz for peak in self._peaks])
        self._intensity = np.concatenate([peak.intensity for peak in self._peaks])
        self._origin = spectrum
        self._startTime = timeRange[0]
        self._endTime = timeRange[1]
        self.calibrator = massCalibrator
        self.calibrated = False
    
    def mz(self):
        if not self.calibrated:
            self._mz = self.calibrator.func.predictMz(self._mz)
            self.calibrated = True
        return self._mz

    def peaks(self):
        if not self.calibrated:
            self._mz = self.calibrator.func.predictMz(self._mz)
            self.calibrated = True
        return self._peaks


class StardardPeak(OribitoolAbstract.StandardPeak):
    pass


class Workspace(object):
    def __init__(self):
        self.filepaths: List[str] = None
        # only differ in this step
        self.showedSpectra1Type: ShowedSpectraType = None
        self.showedSpectra1Filepath: File = None
        self.showedSpectra1: List(Spectrum) = []
        self.showedAveragedSpectra1: AveragedSpectra = None
        self.showedSpectrum1: OribitoolAbstract.Spectrum = None

        self.peakFitFunc: PeakFitFunc = None
        self.calibrationIonList: List[(str, OribitoolFormula.Formula)] = []
        # filepath ->
        # HNO3NO3-,C6H3O2NNO3-,C6H5O3NNO3-,C6H4O5N2NO3-,C8H12O10N2NO3-,C10H17O10N3NO3-
        self.fileCalibrations: Dict[str, CalibrateMass] = {}

        self.calibratedSpectra: List[CalibratedSpectrum] = None
        
