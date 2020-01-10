from typing import List, Union, Tuple
import os
import datetime
import gzip
from enum import Enum
import copy

import scipy.optimize
import numpy as np
import jsonpickle
from bintrees import FastRBTree

import OribitoolAbstract
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


def nullSendStatus(file, msg: str, index: int, length: int):
    '''
    `file`:type is `File`
    '''
    pass


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
    def __init__(self, info, mz, intensity):
        self.info: SpectrumInfo = info
        self._mz: np.ndarray = mz
        self._intensity: np.ndarray = intensity

    @property
    def mz(self):
        return self._mz

    @property
    def intensity(self):
        return self._intensity


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
        return Spectrum(self, *self.info.getSpectrum())


class AveragedSpectrum(OribitoolAbstract.AveragedSpectrum):
    def __init__(self, files: list, timeRanges: List[Tuple[datetime.timedelta, datetime.timedelta]] = None, numRanges: List[Tuple[int, int]] = None):
        self.files = [f for f in files]
        self._averaged = readFileModule.AveragedSpectrum(
            [f._file for f in files], timeRanges, numRanges)


    @property
    def mz(self):
        return self._averaged.mz

    @property
    def intensity(self):
        return self._averaged.intensity

    @property
    def timeRange(self) -> (datetime.datetime, datetime.datetime):
        return self._averaged.timeRange

    @property
    def num(self) -> int:
        return self._averaged.num

    @property
    def timeRanges(self) -> List[Tuple[datetime.datetime, datetime.datetime]]:
        return self._averaged.timeRanges

    @property
    def numRanges(self) -> List[Tuple[int, int]]:
        return self._averaged.numRanges



class AveragedSpectra(OribitoolAbstract.AveragedSpectra):
    def __init__(self, fileList, time: datetime.timedelta = None, N: int = None, sendStatus=nullSendStatus):
        if type(fileList) is not FileList:
            raise TypeError()
        fileList: FileList
        self.fileList = fileList
        self.time = time
        self.N = N
        tree = fileList.filetree
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
                    else:  # left > N
                        numRanges.append((index, index+N-1))
                        index += N
                        left -= N

                    sendStatus(f, msg, len(spectra), total)
                    spectra.append(AveragedSpectrum(
                        toBeProcessed, numRanges=numRanges))
                    # if want to use multi-process, u can add a process pool
                    # and add this to the pool
            except KeyError:
                sendStatus(f, msg, len(spectra), total)
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

                    sendStatus(f, msg, len(spectra), total)
                    spectra.append(AveragedSpectrum(
                        toBeProcessed, timeRanges=timeRanges))
            except KeyError:
                sendStatus(f, msg, len(spectra), total)
                spectra.append(AveragedSpectrum(
                    toBeProcessed, timeRanges=timeRanges))

        sendStatus(f, msg, len(spectra), len(spectra))
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

    def __del__(self):
        pass


class FileList(object):
    '''
    file header list
    '''

    def __init__(self):
        # sorted by start time
        self.filetree = FastRBTree()
        # name -> File
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
    def __init__(self, spectrum: Spectrum, index: int, subscripts: Tuple[int, int]):
        '''
        `subscripts`: (lindex,rindex), both mz[lindex] and mz[rindex] are belong to this peak
        '''
        self._spectrum = spectrum
        self._index = index
        l, r = subscripts
        r += 1
        self._mz: np.ndarray = spectrum.mz[l:r]
        self._intensity: np.ndarray = spectrum.intensity[l:r]

    @property
    def spectrum(self):
        return self._spectrum

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    @property
    def mz(self):
        return self._mz

    @mz.setter
    def mz(self, mz):
        self._mz = mz
        if hasattr(self, '_maxIntensity'):
            delattr(self, '_maxIntensity')

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

    def onlyOnePeak(self) -> bool:
        a = self.intensity
        length = len(a)
        a = a[0:length - 1] < a[1:length]
        length = len(a)
        a = a[0:length - 1] > a[1:length]
        return np.sum(a) == 1


class Peaks(object):
    def __init__(self, spectrum: OribitoolAbstract.Spectrum):
        peaks = []
        begin = 0
        stop = len(spectrum.mz)
        index = 0
        # can split it into several parts and multi-processing them to speed up
        while begin < stop:
            l, r = OribitoolFunc.findPeak(
                spectrum.mz, spectrum.intensity, begin, stop)
            if l < stop:
                peaks.append(Peak(spectrum, index, (l, r)))
                index += 1
            begin = r

        self.peaks = peaks


class PeakFitFunc(object):
    def __init__(self, spectrum: OribitoolAbstract.Spectrum, num: int):
        peaks = Peaks(spectrum)
        peaks=[peak for peak in peaks.peaks if peak.onlyOnePeak()]
        num = max(0, min(num, len(peaks)))

        peaks = sorted(
            peaks, key=lambda peak: peak.maxIntensity, reverse=True)
        peaks = peaks[0:num]
        Func = OribitoolFunc.NormalDistributionFunc
        params: list = [Func.getParam(peak) for peak in peaks]
        normPeaks: List[Peak] = [Func.getNormalizedPeak(
            peaks[index], params[index]) for index in range(num)]

        self.Func=Func
        self.peaks = peaks
        self.params = params
        self.normPeaks = normPeaks
        self.canceled: List[Tuple[Peak, tuple, normPeaks]] = []
        self._func = None

    def rm(self, index):
        peak = self.peaks.pop(index)
        param = self.params.pop(index)
        normPeak = self.normPeaks.pop(index)
        self.canceled.append((peak, param, normPeak))
        self._func = None

    def cancel(self)->Peak:
        if len(self.canceled) == 0:
            return None
        peak, param, normPeak = self.canceled.pop()
        self.peaks.append(peak)
        self.params.append(param)
        self.normPeaks.append(normPeak)
        self._func = None
        return normPeak

    @property
    def func(self) -> OribitoolAbstract.fitPeakFunc:
        if self._func is None and len(self.params)>0:
            self._func = self.Func(self.params)
        return self._func


class Workspace(object):
    def __init__(self):
        self.files = FileList()
        # only differ in this step
        self.showedSpectra1Type: ShowedSpectraType = None
        self.showedSpectra1File: File = None
        self.showedSpectra1: List(Spectrum) = None
        self.showedAveragedSpectra1: AveragedSpectra = None
        self.showedSpectrum1: OribitoolAbstract.Spectrum = None
        self.peakFitFunc: PeakFitFunc = None

    def addFileFromFolder(self, folder, recurrent):
        files = []
        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() == '.raw':
                fullname = os.path.join(folder, f)
                if self.files.addFile(fullname):
                    files.append(fullname)

        if recurrent:
            for f in os.listdir(folder):
                if os.path.isdir(os.path.join(folder, f)):
                    files.extend(self.addFileFromFolder(
                        os.path.join(folder, f), recurrent))

        return files
