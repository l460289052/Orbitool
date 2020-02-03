# -*- coding: utf-8 -*-

import abc
from datetime import datetime, timedelta
from typing import List, Tuple, Union

import numpy as np

class Formula(abc.ABC):
    @abc.abstractmethod
    def __init__(self, formula: str = None):
        pass

    @abc.abstractmethod
    def mass(self) -> float:
        pass

    @abc.abstractmethod
    def __eq__(self, formula):
        pass

    @abc.abstractmethod
    def __hash__(self):
        pass

class File(abc.ABC):
    @abc.abstractmethod
    def __init__(self, fullname):
        pass

    @property
    @abc.abstractmethod
    def getSpectrumInfo(self, scanNum):
        pass

    @property
    @abc.abstractmethod
    def creationDate(self) -> datetime:
        pass

    @property
    @abc.abstractmethod
    def startTime(self) -> timedelta:
        pass

    @property
    @abc.abstractmethod
    def endTime(self) -> timedelta:
        pass

    @property
    @abc.abstractmethod
    def firstScanNumber(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def lastScanNumber(self) -> int:
        pass

    def __del__(self):
        pass


class Spectrum(abc.ABC):
    @abc.abstractmethod
    def __init__(self, mz: np.ndarray, intensity: np.ndarray):
        pass

    @property
    def mz(self):
        return self._mz

    @property
    def intensity(self):
        return self._intensity


class SpectrumInfo(abc.ABC):
    @abc.abstractmethod
    def __init__(self, file, scanNum):
        pass

    @property
    @abc.abstractmethod
    def retentionTime(self) -> timedelta:
        pass

    @property
    @abc.abstractmethod
    def scanFilter(self):
        pass

    @abc.abstractmethod
    def getSpectrum(self) -> Spectrum:
        pass


class AveragedSpectrum(Spectrum):
    @abc.abstractmethod
    def __init__(self, file: File, timeRange: Tuple[timedelta, timedelta] = None, numRange: Tuple[int, int] = None):
        '''
        numRange include left and right spectrum
        '''
        pass

    @property
    def timeRange(self) -> (datetime, datetime):
        return self._timeRange

    @property
    def numRange(self) -> Tuple[int, int]:
        return self._numRange


def nullSendStatus(fileTime, msg, index, length):
    pass


class AveragedSpectra(abc.ABC):
    @abc.abstractmethod
    def __init__(self, fileList, time: timedelta = None, N: int = None, sendStatus=nullSendStatus):
        pass


class Peak(abc.ABC):
    @abc.abstractmethod
    def __init__(self, spectrum: Spectrum, indexRange: range, mz=None, intensity=None):
        pass

    @property
    def spectrum(self) -> Spectrum:
        return self._spectrum

    @property
    def mz(self) -> np.ndarray:
        return self._mz[self._indexRange]

    @property
    def intensity(self) -> np.ndarray:
        return self._intensity[self._indexRange]

    @property
    @abc.abstractmethod
    def maxIntensity(self):
        pass

    @abc.abstractmethod
    def peakAt(self) -> np.ndarray:
        pass

    @property
    @abc.abstractmethod
    def peaksNum(self) -> int:
        pass


class FitPeakFunc(abc.ABC):
    @abc.abstractmethod
    def __init__(self, paramList: List[tuple]):
        pass

    @staticmethod
    @abc.abstractmethod
    def _func(mz, param):
        pass

    @staticmethod
    @abc.abstractmethod
    def getParam(peak: Peak):
        pass

    @staticmethod
    @abc.abstractmethod
    def getNormalizedPeak(peak: Peak, param: tuple) -> Tuple[np.ndarray,np.ndarray]:
        pass

    @abc.abstractmethod
    def normFunc(self, x: np.ndarray):
        pass

    @abc.abstractmethod
    def _funcFit(self, mz, param):
        pass

    @abc.abstractmethod
    def getFittedParam(self, peak: Peak):
        pass

    @abc.abstractmethod
    def getPeakPosition(self, fittedPeak):
        pass

    @abc.abstractmethod
    def getPeakIntensity(self, fittedPeak):
        pass

    @abc.abstractmethod
    def getArea(self, fittedPeak):
        pass

    @abc.abstractmethod
    def splitPeakAsParams(self, peak: Peak, num=None, force=False):
        if isinstance(peak, FittedPeak):
            raise ValueError('please use original peak')
        pass


class FittedPeak(Peak):
    @abc.abstractmethod
    def __init__(self, originalPeak: Peak, fitPeakFunc: FitPeakFunc, fittedParam=None):
        pass

    @property
    def fittedParam(self):
        return self._param

    @property
    def peakPosition(self):
        return self._peakPosition

    @property
    def peakIntensity(self):
        return self._peakIntensity

    @property
    def area(self):
        return self._area


class MassCalibrationFunc(abc.ABC):
    @abc.abstractmethod
    def __init__(self, mz: np.ndarray, ppm: np.ndarray, args):
        pass

    @abc.abstractmethod
    def predictPpm(self, mz):
        pass

    @abc.abstractmethod
    def predictMz(self, mz):
        pass

    @abc.abstractmethod
    def __str__(self):
        pass


class CalibratedSpectrum(Spectrum):

    @property
    def fileTime(self) -> str:
        return self._fileTime

    @property
    def originalSpectrum(self) -> Spectrum:
        return self._origin

    @property
    def peaks(self) -> List[Peak]:
        '''
        warning: not fitted peak
        '''
        return self._peaks

    @property
    def startTime(self) -> datetime:
        return self._startTime

    @property
    def endTime(self) -> datetime:
        return self._endTime

    @property
    @abc.abstractmethod
    def mz(self) -> np.ndarray:
        pass

    @property
    @abc.abstractmethod
    def intensity(self) -> np.ndarray:
        pass

class CalibratedPeak(Peak):
    @abc.abstractmethod
    def __init__(self, mz: np.ndarray, intensity: np.ndarray, indexRange: range, originalPeak: Peak):
        pass

class StandardPeak(abc.ABC):
    def __init__(self, peakPosition: float, formulaList: list,subpeaks:int, isStart:bool=True, handled=False):
        self._peakPosition = peakPosition
        self._formulaList = formulaList
        self._subpeaks=subpeaks
        self._isStart = isStart
        self._handled = handled

    @property
    def peakPosition(self) -> float:
        return self._peakPosition

    @peakPosition.setter
    def peakPosition(self, peakPosition):
        self._peakPosition = peakPosition

    @property
    def formulaList(self) -> List[Formula]:
        return self._formulaList

    @formulaList.setter
    def formulaList(self, formulaList):
        self._formulaList = formulaList

    @property
    def isStart(self) -> int:
        '''
        fitted peaks are crossed, if it's the first peak of fitted peaks
        isStart will be true, else false.
        peak1           :True
          peak2         :False
           peak3        :False
                 peak4  :True
        '''
        return self._isStart

    @isStart.setter
    def isStart(self, isStart):
        self._isStart = isStart

    @property
    def subpeaks(self) -> int:
        return self._subpeaks

    @subpeaks.setter
    def subpeaks(self, subpeaks):
        self._subpeaks = subpeaks

    @property
    def handled(self):
        return self._handled
    
    @handled.setter
    def handled(self, handled):
        self._handled = handled

class MassList(abc.ABC):
    def __init__(self, ppm=5e-7):
        self.ppm = 1e-6
        self._peaks: List[StandardPeak] = []

    @abc.abstractmethod
    def addPeaks(self, peaks:Union[StandardPeak,List[StandardPeak]]):
        pass

    def popPeaks(self, indexes: Union[int, List[int]]):
        if isinstance(indexes, int):
            indexes = [indexes]
        else:
            indexes=indexes.copy()
            indexes.sort(reverse=True)
        poped = []
        for index in indexes:
            poped.append(indexes.pop(index))
        poped.reverse()
        return poped

    def __getitem__(self, index: Union[int, slice, range]) -> Union[StandardPeak, List[StandardPeak]]:
        if isinstance(index, (int, slice)):
            return self._peaks[index]
        elif isinstance(index, range):
            return self._peaks[index.start:index.stop:index.step]

    def __iter__(self):
        return iter(self._peaks)

    def __len__(self):
        return len(self._peaks)
