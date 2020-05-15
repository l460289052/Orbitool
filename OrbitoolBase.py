# -*- coding: utf-8 -*-

import abc
from datetime import datetime, timedelta
from typing import List, Tuple, Union, Iterable
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
        newPeaks = []
        for peak in peaks:
            newPeak = MassListPeak(
                peak.peakPosition, peak.formulaList, peak.splitNum, peak.handled)
            if newPeak.formulaList is None:
                newPeak.formulaList = []
            if len(newPeak.formulaList) == 1:
                newPeak.peakPosition = newPeak.formulaList[0].mass()
            newPeaks.append(newPeak)
        newPeaks.sort(key=lambda peak: peak.peakPosition)
        peaks1 = self._peaks
        peaks2 = newPeaks
        iter1 = iterator(peaks1)
        iter2 = iterator(peaks2)
        peaks = []
        ppm = self.ppm
        while not (iter1.end and iter2.end):
            if iter1.end:
                peaks.extend(peaks2[iter2.index:])
                break
            if iter2.end:
                peaks.extend(peaks1[iter1.index:])
                break
            peak1: MassListPeak = iter1.value
            peak2: MassListPeak = iter2.value
            if abs(peak2.peakPosition / peak1.peakPosition - 1) < ppm:
                if peak1.handled and not peak2.handled:
                    peaks.append(peak1)
                elif not peak1.handled and peak2.handled:
                    peaks.append(peak2)
                else:
                    if peak1.formulaList == peak2.formulaList:
                        peak = MassListPeak((peak1.peakPosition + peak2.peakPosition) / 2, peak1.formulaList, max(peak1.splitNum, peak2.splitNum), peak1.handled)
                        peaks.append(peak)
                    elif peak1.handled and peak2.handled:
                        raise ValueError("can't merge peak in mass list at %.5f with peak at %.5f using ppm = %.2f" % (
                            peak1.peakPosition, peak2.peakPosition, ppm*1e6))
                    elif len(peak1.formulaList) < len(peak2.formulaList):
                        peaks.append(peak1)
                    elif len(peak1.formulaList) > len(peak2.formulaList):
                        peaks.append(peak2)
                    else:
                        formulaList = list(
                            set(peak1.formulaList) & set(peak2.formulaList))
                        formulaList.sort(key=lambda formula: formula.mass())
                        if len(formulaList) == 1:
                            peak = MassListPeak(formulaList[0].mass(), formulaList, max(peak1.splitNum, peak2.splitNum))
                        else:
                            peak = MassListPeak((peak1.peakPosition + peak2.peakPosition) / 2, formulaList, max(peak1.splitNum, peak2.splitNum))
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

    def popPeaks(self, indexes: Union[int, List[int]]):
        if isinstance(indexes, int):
            indexes = [indexes]
        else:
            indexes = indexes.copy()
            indexes.sort(reverse=True)
        poped = []
        peaks = self._peaks
        for index in indexes:
            poped.append(peaks.pop(index))
        poped.reverse()
        return poped

    def __getitem__(self, index: Union[int, slice, range]) -> Union[Peak, List[Peak]]:
        if isinstance(index, (int, slice)):
            return self._peaks[index]
        elif isinstance(index, range):
            return self._peaks[index.start:index.stop:index.step]

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
