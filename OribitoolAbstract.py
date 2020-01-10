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
        pass

    @abc.abstractmethod
    def getSpectrumInfo(self, scanNum):
        pass

    @abc.abstractmethod
    def __del__(self):
        pass


class FileHeader(abc.ABC):
    @abc.abstractmethod
    def __init__(self, file):
        pass

    @property
    @abc.abstractmethod
    def file(self):
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


class Spectrum(abc.ABC):
    @abc.abstractmethod
    def __init__(self, info, mz: np.ndarray, intensity: np.ndarray):
        pass

    @property
    @abc.abstractmethod
    def mz(self):
        pass

    @property
    @abc.abstractmethod
    def intensity(self):
        pass


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
    @abc.abstractmethod
    def num(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def timeRange(self) -> (datetime, datetime):
        pass

    @property
    @abc.abstractmethod
    def timeRanges(self) -> List[Tuple[datetime, datetime]]:
        pass

    @property
    @abc.abstractmethod
    def numRanges(self) -> List[Tuple[int, int]]:
        pass
    


def nullSendStatus(file, msg, index, length):
    pass


class AveragedSpectra(abc.ABC):
    @abc.abstractmethod
    def __init__(self, fileList, time: timedelta = None, N: int = None, sendStatus=nullSendStatus):
        pass


class Peak(abc.ABC):
    @abc.abstractmethod
    def __init__(self, spectrum: Spectrum, index: int, subscripts: Tuple[int, int]):
        pass

    @property
    @abc.abstractmethod
    def spectrum(self) -> Spectrum:
        pass

    @property
    @abc.abstractmethod
    def index(self) -> int:
        pass

    @index.setter
    @abc.abstractmethod
    def index(self, index):
        pass

    @property
    @abc.abstractmethod
    def mz(self) -> np.ndarray:
        pass

    @mz.setter
    @abc.abstractmethod
    def mz(self, mz):
        pass

    @property
    @abc.abstractmethod
    def intensity(self) -> np.ndarray:
        pass

    @intensity.setter
    @abc.abstractmethod
    def intensity(self, intensity):
        pass

    @property
    @abc.abstractmethod
    def maxIntensity(self):
        pass

    @abc.abstractmethod
    def onlyOnePeak(self) -> bool:
        pass


class fitPeakFunc(abc.ABC):
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
    def normFunc(self,x:np.ndarray):
        pass

    @abc.abstractmethod
    def _funcFit(self, mz, param):
        pass

    @abc.abstractmethod
    def getFittedParam(self, peak: Peak):
        pass

    @abc.abstractmethod
    def getFittedPeak(self, peak: Peak, fittedParam: tuple = None) -> Peak:
        pass
