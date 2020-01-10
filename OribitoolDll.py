# -*- coding: utf-8 -*-

import OribitoolAbstract
import OribitoolFunc

import os
import copy
import datetime
from typing import List, Tuple

import numpy as np
import clr


clr.AddReference(os.path.join(os.getcwd(), 'ThermoFisher.CommonCore.Data.dll'))
clr.AddReference(os.path.join(
    os.getcwd(), 'ThermoFisher.CommonCore.RawFileReader.dll'))
clr.AddReference(os.path.join(
    os.getcwd(), 'ThermoFisher.CommonCore.BackgroundSubtraction.dll'))
clr.AddReference(os.path.join(
    os.getcwd(), 'ThermoFisher.CommonCore.MassPrecisionEstimator.dll'))

clr.AddReference('System.Collections')

from ThermoFisher.CommonCore.Data import ToleranceUnits
from ThermoFisher.CommonCore.Data import Extensions
from ThermoFisher.CommonCore.Data.Business import ChromatogramSignal, ChromatogramTraceSettings, DataUnits, Device, GenericDataTypes, SampleType, Scan, TraceType
from ThermoFisher.CommonCore.Data.FilterEnums import IonizationModeType, MSOrderType
from ThermoFisher.CommonCore.Data.Interfaces import IChromatogramSettings, IScanEventBase, IScanFilter, RawFileClassification
from ThermoFisher.CommonCore.MassPrecisionEstimator import PrecisionEstimate
from ThermoFisher.CommonCore.RawFileReader import RawFileReaderAdapter

class FileHeader(OribitoolAbstract.FileHeader):
    def __init__(self, file):
        self._rawfile = file.rawfile
        self._file = file

    @property
    def file(self):
        return self._file

    @property
    def rawfile(self):
        return self._rawfile

    @property
    def creationDate(self) -> datetime.datetime:
        time = self.rawfile.FileHeader.CreationDate
        d = datetime.datetime(year=time.Year, month=time.Month, day=time.Day, hour=time.Hour,
                              minute=time.Minute, second=time.Second, microsecond=time.Millisecond*1000)
        return d
        # self.creationDate=datetime.datetime.min+datetime.timedelta(milliseconds=f.FileHeader.CreationDate.Ticks/10)

    @property
    def startTime(self) -> datetime.timedelta:
        return datetime.timedelta(minutes=self.rawfile.RunHeader.StartTime)

    @property
    def endTime(self) -> datetime.timedelta:
        return datetime.timedelta(minutes=self.rawfile.RunHeader.EndTime)

    @property
    def firstScanNumber(self) -> int:
        return self.rawfile.RunHeader.FirstSpectrum

    @property
    def lastScanNumber(self) -> int:
        return self.rawfile.RunHeader.LastSpectrum


class SpectrumInfo(OribitoolAbstract.SpectrumInfo):
    def __init__(self, file, scanNum):
        self.file = file
        self.rawfile = file.rawfile
        self.scanNum = scanNum

    @property
    def retentionTime(self) -> datetime.timedelta:
        '''
        return minutes from begin
        '''
        return datetime.timedelta(minutes=self.rawfile.RetentionTimeFromScanNumber(self.scanNum))

    @property
    def scanFilter(self):
        pass
        # return IScanFilter(self.rawfile.GetFilterForScanNumber(self.scanNum))

    def getSpectrum(self) -> (np.ndarray, np.ndarray):
        '''
        return (mz, intensity)
        '''
        rawfile = self.rawfile
        scanNum = self.scanNum
        scanStatistics = rawfile.GetScanStatsForScanNumber(scanNum)

        segmentedScan = rawfile.GetSegmentedScanFromScanNumber(
            scanNum, scanStatistics)
        return np.array(list(segmentedScan.Positions)), np.array(list(segmentedScan.Intensities))


class AveragedSpectrum(OribitoolAbstract.AveragedSpectrum):
    def __init__(self, files: list, timeRanges: List[Tuple[datetime.timedelta, datetime.timedelta]] = None, numRanges: List[Tuple[int, int]] = None):
        timeRanges = copy.copy(timeRanges)
        numRanges = copy.copy(numRanges)
        averaged = None

        def method(f, index: int) -> datetime.timedelta:
            return f.getSpectrumInfo(index).retentionTime
        if len(files) == 1:
            # single file
            f: File = files[0]
            h = f.header
            start = None
            end = None
            if timeRanges is not None and numRanges is None:
                r: range = OribitoolFunc.indexBetween(f, timeRanges[0],
                                                      (h.firstScanNumber,
                                                       h.lastScanNumber + 1),
                                                      method=method)
                start = r.start
                end = r.stop-1
            elif numRanges is not None and timeRanges is None:
                start, end = numRanges[0]
            else:
                raise ValueError(
                    "`timeRange` or `numRanges` must be provided and only one can be provided")
            scanfilter = IScanFilter(f.rawfile.GetFilterForScanNumber(start))
            averaged = Extensions.AverageScansInScanRange(
                f.rawfile, start, end, scanfilter).SegmentedScan
        else:
            f: File = None
            start = None
            end = None
            if timeRanges is not None and numRanges is None:
                maxIndex = 0
                diff = timeRanges[0][1] - timeRanges[0][0]
                for index in range(1, len(timeRanges)):
                    s, e = timeRanges[index]
                    if diff < e - s:
                        maxIndex = index
                        diff = e - s
                f = files[maxIndex]
                h = f.header
                r: range = OribitoolFunc.indexBetween(f, timeRanges[maxIndex],
                                                      (h.firstScanNumber,
                                                       h.lastScanNumber + 1),
                                                      method=method)
                start = r.start
                end = r.stop-1
            elif numRanges is not None and timeRanges is None:
                maxIndex = 0
                diff = numRanges[0][1] - numRanges[0][0]
                for index in range(1, len(numRanges)):
                    s, e = numRanges[index]
                    if diff < e - s:
                        maxIndex = index
                        diff = e - s
                f = files[index]
                start, end = numRanges[index]
            else:
                raise ValueError(
                    "`timeRange` or `numRanges` must be provided and only one can be provided")
            scanfilter = f.rawfile.GetFilterForScanNumber(start)
            averaged = Extensions.AverageScansInScanRange(
                f.rawfile, start, end, scanfilter).SegmentedScan

        sTime = None
        eTime = None
        num = 0
        for index in range(len(files)):
            f: File = files[index]
            h = f.header
            start = None
            end = None
            if timeRanges is not None:
                r: range = OribitoolFunc.indexBetween(f, timeRanges[index], (
                    h.firstScanNumber, h.lastScanNumber + 1), method=method)
                start = r.start
                end = r.stop - 1
            elif numRanges is not None:
                start, end = numRanges[index]
            num += end-start+1
            stime = h.creationDate + f.getSpectrumInfo(start).retentionTime
            etime = h.creationDate + f.getSpectrumInfo(end).retentionTime
            if sTime is None or sTime > stime:
                sTime = stime
            if eTime is None or eTime < etime:
                eTime = etime
        self._timeRange = (sTime, eTime)
        self._num = num

        self.files = files
        self._timeRanges = timeRanges
        self._numRanges = timeRanges
        self._mz = np.array(list(averaged.Positions))
        self._intensity = np.array(list(averaged.Intensities))

    @property
    def mz(self) -> np.ndarray:
        return self._mz

    @property
    def intensity(self) -> np.ndarray:
        return self._intensity

    @property
    def num(self) -> int:
        return self._num

    @property
    def timeRange(self) -> (datetime.datetime, datetime.datetime):
        return self._timeRange

    @property
    def timeRanges(self) -> List[Tuple[datetime.datetime, datetime.datetime]]:
        return self._timeRanges

    @property
    def numRanges(self) -> List[Tuple[int, int]]:
        return self._numRanges


class File(OribitoolAbstract.File):
    def __init__(self, fullname):
        rawfile = RawFileReaderAdapter.FileFactory(fullname)
        rawfile.SelectInstrument(Device.MS, 1)
        self._rawfile = rawfile
        self._header = FileHeader(self)

    @property
    def rawfile(self):
        return self._rawfile

    @property
    def header(self) -> FileHeader:
        return self._header

    def getSpectrumInfo(self, scanNum):
        return SpectrumInfo(self, scanNum)

    def __del__(self):
        self._rawfile.Dispose()
