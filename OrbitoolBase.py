# -*- coding: utf-8 -*-

import abc
from datetime import datetime, timedelta
from typing import List, Tuple, Union, Iterable
from sortedcontainers import SortedKeyList
from OrbitoolFormula import FormulaHint
from OrbitoolFormulaCalc import IonCalculatorHint

import numpy as np

def nullSendStatus(fileTime: datetime, msg: str, index: int, length: int):
    pass


class Spectrum:
    def __init__(self, fileTime: datetime, mz: np.ndarray, intensity: np.ndarray, timeRange: (datetime, datetime), numRange: (int, int), originalSpectrum=None, peaks=None):
        self.fileTime = fileTime
        self.mz = mz
        self.intensity = intensity
        self.timeRange = timeRange
        self.numRange = numRange
        self.originalSpectrum = originalSpectrum
        self.peaks: List[Peak] = peaks


class Peak:
    def __init__(self, spectrum: Spectrum, indexRange: range = None, mz=None, intensity=None, originalPeak=None, splitNum=None):
        self.spectrum = spectrum
        if indexRange is not None:
            self._mz = spectrum.mz
            self._intensity = spectrum.intensity
            self._indexRange = indexRange
        elif mz is not None:
            self._mz = mz
            self._intensity = intensity
            self._indexRange = range(len(mz))
        else:
            self._mz = None
            self._intensity = None
            self._indexRange = None
        self.originalPeak = originalPeak
        self._splitNum = splitNum
        self.handled = False

    def addFittedParam(self, fittedParam=None, peakPosition=None, peakIntensity=None, area=None):
        self.fittedParam = fittedParam
        self.peakPosition = peakPosition
        self.peakIntensity = peakIntensity
        self.area = area

    def addFormula(self, formulaList: List[FormulaHint]):
        self.formulaList = formulaList

    def copy(self, spectrum=None, indexRange: range = None, mz=None, intensity=None):
        peak = None
        if spectrum is None:
            peak = Peak(self.spectrum, self._indexRange, self.originalPeak)
        else:
            peak = Peak(spectrum, indexRange, mz, intensity, self.originalPeak)
        if hasattr(self, 'fittedParam'):
            peak.addFittedParam(
                self.fittedParam, self.peakPosition, self.peakIntensity, self.area)
        if hasattr(self, 'formulaList'):
            peak.addFormula(self.formulaList)
        return peak

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
        if hasattr(self, '_peakAt'):
            return getattr(self, '_peakAt')
        a = self.intensity
        a = a[:-1] < a[1:]
        a = a[:-1] > a[1:]
        self._peakAt = a
        return a

    @property
    @abc.abstractmethod
    def splitNum(self) -> int:
        if self._splitNum is None:
            self._splitNum = np.sum(self.peakAt())
        return self._splitNum


class iterator:
    def __init__(self, l: Iterable):
        self._iter = iter(l)
        try:
            self._value = next(self._iter)
            self._end = False
        except StopIteration:
            self._value = None
            self._end = True
        self._index = 0

    @property
    def index(self):
        return self._index

    @property
    def value(self):
        return self._value if not self.end else None

    @property
    def end(self) -> bool:
        return self._end

    def next(self):
        if not self.end:
            try:
                self._value = next(self._iter)
            except StopIteration:
                self._end = True
            self._index += 1


class MassListPeak:
    def __init__(self, peakPosition, formulaList, splitNum=1, handled=False):
        self.peakPosition = peakPosition
        self.formulaList = formulaList
        self.splitNum = splitNum
        self.handled = handled


class MassList:
    def __init__(self, ppm=5e-7):
        self.ppm = ppm
        self._peaks: List[MassListPeak] = []

    def addPeaks(self, peaks: Union[Peak, List[Peak], MassListPeak, List[MassListPeak]]):
        if not isinstance(peaks, Iterable):
            peaks = [peaks]

        def getPeakPosition(peak: Peak):
            return peak.peakPosition
        def calcPpm(peak1, peak2):
            return abs(peak1.peakPosition/peak2.peakPosition-1)
        newPeaks = []
        for peak in peaks:
            newPeak = MassListPeak(
                peak.peakPosition, peak.formulaList, peak.splitNum, peak.handled)
            if newPeak.formulaList is None:
                newPeak.formulaList = []
            if len(newPeak.formulaList) == 1:
                newPeak.peakPosition = newPeak.formulaList[0].mass()
            newPeaks.append(newPeak)
        peaks = self._peaks
        peaks.extend(newPeaks)
        newPeaks = SortedKeyList(key=getPeakPosition)
        for peak in peaks:
            right = newPeaks.bisect_left(peak)
            left = right-1
            if left < 0:
                if len(newPeaks) == 0:
                    newPeaks.add(peak)
                    continue
                else:
                    fIndex = right
                    fPpm = calcPpm(peak, newPeaks[right])
            elif right == len(newPeaks):
                fIndex = left
                fPpm = calcPpm(peak, newPeaks[left])
            else:
                lPpm = calcPpm(peak, newPeaks[left])
                rPpm = calcPpm(peak, newPeaks[right])
                if lPpm < rPpm:
                    fPpm = lPpm
                    fIndex = left
                else:
                    fPpm = rPpm
                    fIndex = right

            if fPpm > self.ppm:
                newPeaks.add(peak)
            else:
                fPeak = newPeaks[fIndex]
                if peak.formulaList != fPeak.formulaList:
                    if len(peak.formulaList) != 0:
                        if len(fPeak.formulaList) == 0:
                            newPeaks.pop(fIndex)
                        newPeaks.add(peak)

        self._peaks = list(newPeaks)

    def popPeaks(self, indexes: Union[int, List[int]]):
        if isinstance(indexes, int):
            indexes = [indexes]
        else:
            indexes = indexes.copy()
        indexes = np.unique(indexes)
        poped = []
        peaks = self._peaks
        for index in indexes[::-1]:
            poped.append(peaks.pop(index))
        poped.reverse()
        return poped

    def __getitem__(self, index: Union[int, slice, range]) -> Union[Peak, List[Peak]]:
        if isinstance(index, range):
            return self._peaks[index.start:index.stop:index.step]
        else:
            return self._peaks[index]

    def __iter__(self):
        return iter(self._peaks)

    def __len__(self):
        return len(self._peaks)


class TimeSeries:
    def __init__(self, time: np.ndarray, intensity: np.ndarray, mz: float, ppm: float, tag: str):
        # np.datetime64
        self.time = time
        self.intensity = intensity
        self.mz = mz
        self.ppm = ppm
        self.tag = tag


class Operator(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args):
        pass

    @abc.abstractmethod
    def __call__(self, sendStatus=nullSendStatus):
        return self.process(sendStatus)
