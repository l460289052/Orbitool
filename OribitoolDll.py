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
    def __init__(self, file:OribitoolAbstract.File, timeRange: Tuple[datetime.timedelta, datetime.timedelta] = None, numRange: Tuple[int, int] = None):
        averaged = None

        def method(f, index: int) -> datetime.timedelta:
            return f.getSpectrumInfo(index).retentionTime


        start = None
        end = None
        if timeRange is not None and numRange is None:
            r: range = OribitoolFunc.indexBetween(file, timeRange,
                                                    (file.firstScanNumber,
                                                    file.lastScanNumber + 1),
                                                    method=method)
            start = r.start
            end = r.stop
        elif numRange is not None and timeRange is None:
            start, end = numRange
        else:
            raise ValueError(
                "`timeRange` or `numRange` must be provided and only one can be provided")
        scanfilter = IScanFilter(file.rawfile.GetFilterForScanNumber(start))
        last = end - 1
        averaged = Extensions.AverageScansInScanRange(
            file.rawfile, start, last, scanfilter).SegmentedScan

        sTime = file.creationDate + file.getSpectrumInfo(start).retentionTime
        eTime = file.creationDate + file.getSpectrumInfo(last).retentionTime

        self._timeRange = (sTime, eTime)

        self.file = file
        self._numRange = (start,end)
        self._mz = np.array(list(averaged.Positions))
        self._intensity = np.array(list(averaged.Intensities))

class File(OribitoolAbstract.File):
    def __init__(self, fullname):
        rawfile = RawFileReaderAdapter.FileFactory(fullname)
        rawfile.SelectInstrument(Device.MS, 1)
        self._rawfile = rawfile

    @property
    def rawfile(self):
        return self._rawfile

    def getSpectrumInfo(self, scanNum):
        return SpectrumInfo(self, scanNum)

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

    def __del__(self):
        self._rawfile.Dispose()
