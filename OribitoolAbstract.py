# -*- coding: utf-8 -*-

import abc
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np


class File(abc.ABC):
    @abc.abstractmethod
    def __init__(self, fullname):
        pass

    @property
    @abc.abstractmethod
    def header(self):
        return self._header

    @abc.abstractmethod
    def getSpectrumInfo(self, scanNum):
        pass

    def __del__(self):
        pass


class FileHeader(abc.ABC):
    @abc.abstractmethod
    def __init__(self, file):
        pass

    @property
    def file(self):
        return self._file

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
    def __init__(self, files: List[File], timeRanges: List[Tuple[timedelta, timedelta]] = None, numRanges: List[Tuple[int, int]] = None):
        pass

    @property
    def num(self) -> int:
        return self._num

    @property
    def timeRange(self) -> (datetime, datetime):
        return self._timeRange

    @property
    def timeRanges(self) -> List[Tuple[datetime, datetime]]:
        return self._timeRanges

    @property
    def numRanges(self) -> List[Tuple[int, int]]:
        return self._numRanges


def nullSendStatus(filepath, msg, index, length):
    pass


class AveragedSpectra(abc.ABC):
    @abc.abstractmethod
    def __init__(self, fileList, time: timedelta = None, N: int = None, sendStatus=nullSendStatus):
        pass


class Peak(abc.ABC):
    @abc.abstractmethod
    def __init__(self, spectrum: Spectrum, subscripts: Tuple[int, int]):
        pass

    @property
    def spectrum(self) -> Spectrum:
        return self._spectrum

    @property
    def mz(self) -> np.ndarray:
        return self._mz

    @mz.setter
    def mz(self, mz):
        self._mz = mz

    @property
    def intensity(self) -> np.ndarray:
        return self._intensity

    @intensity.setter
    def intensity(self, intensity):
        self._intensity = intensity

    @property
    @abc.abstractmethod
    def maxIntensity(self):
        pass

    @abc.abstractmethod
    def peakAt(self) -> np.ndarray:
        pass

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
    def getNormalizedPeak(peak: Peak, param: tuple) -> Peak:
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
    def splitPeakAsParams(self, peak: Peak, num=None):
        if issubclass(type(peak), FittedPeak):
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
    def originalSpectrum(self) -> Spectrum:
        return self._origin

    @property
    def peaks(self) -> List[Peak]:
        '''
        warning: not fitted peak
        '''
        return self._peaks
        
    @property
    def startTime(self)->datetime:
        return self._startTime

    @property
    def endTime(self)->datetime:
        return self._endTime

    @property
    @abc.abstractmethod
    def mz(self)->np.ndarray:
        pass

    @property
    @abc.abstractmethod
    def intensity(self)->np.ndarray:
        pass
        


class StandardPeak(abc.ABC):
    def __init__(self, peakPosition, formula, subpeaks):
        self._peakPosition = peakPosition
        self._formula = formula
        self._subpeaks=subpeaks

    @property
    def peakPosition(self) -> float:
        return self._peakPosition

    @peakPosition.setter
    def peakPosition(self, peakPosition):
        self._peakPosition = peakPosition

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, formula):
        self._formula = formula

    @property
    def subpeaks(self) -> int:
        return self._subpeaks

    @subpeaks.setter
    def subpeaks(self, subpeaks):
        self._subpeaks = subpeaks
