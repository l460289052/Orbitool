# -*- coding: utf-8 -*-

from functools import cached_property
from ... import functions

import os
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
from Orbitool import setting
match setting.file.dotnet_driver:
    case ".net framework":
        pass
    case ".net core":
        from pythonnet import load
        load("coreclr")
import clr


pwd = os.path.dirname(__file__)
clr.AddReference(os.path.join(pwd, 'ThermoFisher.CommonCore.Data.dll'))
clr.AddReference(os.path.join(
    pwd, 'ThermoFisher.CommonCore.RawFileReader.dll'))
clr.AddReference(os.path.join(
    pwd, 'ThermoFisher.CommonCore.BackgroundSubtraction.dll'))
clr.AddReference(os.path.join(
    pwd, 'ThermoFisher.CommonCore.MassPrecisionEstimator.dll'))

clr.AddReference('System.Collections')

from ThermoFisher.CommonCore.RawFileReader import RawFileReaderAdapter
from ThermoFisher.CommonCore.MassPrecisionEstimator import PrecisionEstimate
from ThermoFisher.CommonCore.Data.Interfaces import IChromatogramSettings, IScanEventBase, \
    IScanFilter, RawFileClassification
from ThermoFisher.CommonCore.Data.FilterEnums import IonizationModeType, MSOrderType, PolarityType
from ThermoFisher.CommonCore.Data.Business import ChromatogramSignal, ChromatogramTraceSettings, \
    DataUnits, Device, GenericDataTypes, SampleType, Scan, TraceType, MassOptions
from ThermoFisher.CommonCore.Data import ToleranceUnits, Extensions

convertPolarity = {PolarityType.Any: 0,
                   PolarityType.Positive: 1,
                   PolarityType.Negative: -1}


def initRawFile(path):
    rawfile = RawFileReaderAdapter.FileFactory(str(path))
    rawfile.SelectInstrument(Device.MS, 1)
    rawfile.IncludeReferenceAndExceptionData = True
    return rawfile


class File:
    def __init__(self, fullname):
        assert os.path.exists(fullname), f"File not exists: {fullname}"
        self.path = fullname
        self.name = os.path.split(fullname)[1]
        self.rawfile = initRawFile(fullname)

        # time doesn't contain time zone info
        time = self.rawfile.FileHeader.CreationDate
        self.creationDatetime = datetime(year=time.Year, month=time.Month, day=time.Day, hour=time.Hour,
                                         minute=time.Minute, second=time.Second, microsecond=time.Millisecond * 1000)
        self.startTimedelta = timedelta(
            minutes=self.rawfile.RunHeader.StartTime)
        self.endTimedelta = timedelta(
            minutes=self.rawfile.RunHeader.EndTime)
        self.firstRawScanNum = self.rawfile.RunHeader.FirstSpectrum
        self.lastRawScanNum = self.rawfile.RunHeader.LastSpectrum
        extra_info = self.rawfile.GetTrailerExtraInformation(1)
        extra_info_dict = dict(zip(extra_info.Labels, extra_info.Values))
        self.massResolution = float(extra_info_dict.get("FT Resolution:"))

    @cached_property
    def startDatetime(self):
        return self.creationDatetime + self.startTimedelta

    @cached_property
    def endDatetime(self):
        return self.creationDatetime + self.endTimedelta

    @cached_property
    def totalScanNum(self):
        return self.lastRawScanNum - self.firstRawScanNum + 1

    def getRawScanNum(self, scan_num):
        return int(scan_num) + self.firstRawScanNum

    def getSpectrumRetentionTime(self, scanNum):
        rawScanNum = self.getRawScanNum(scanNum)
        retentionTime = timedelta(
            minutes=self.rawfile.RetentionTimeFromScanNumber(rawScanNum))
        if rawScanNum == self.lastRawScanNum:
            lastRetentionTime = self.getSpectrumRetentionTime(scanNum - 1)
            if retentionTime < lastRetentionTime:
                averageTimeDelta = (self.endTimedelta - self.startTimedelta) / \
                    (self.lastRawScanNum - self.firstRawScanNum)
                retentionTime = lastRetentionTime + averageTimeDelta
        return timedelta(minutes=self.rawfile.RetentionTimeFromScanNumber(rawScanNum))

    def getSpectrumRetentionTimes(self):
        return [self.getSpectrumRetentionTime(raw_scan_num) for raw_scan_num in range(self.firstRawScanNum, self.lastRawScanNum + 1)]

    def getSpectrumDatetime(self, scanNum):
        return self.creationDatetime + self.getSpectrumRetentionTime(scanNum)

    def checkFilter(self, polarity) -> bool:
        for f in self.rawfile.GetFilters():
            if convertPolarity[f.Polarity] == polarity:
                return True
        return False

    def getFilter(self, start, stop, polarity):
        scanfilters = self.rawfile.GetFiltersForScanRange(start, stop - 1)
        # if convertPolarity[scanfilter.Polarity] == polarity:
        #     return scanfilter
        return None

    def getFilterInTimeRange(self, start: float, end: float, polarity):
        scanfilters = Extensions.GetFiltersForTimeRange(
            self.rawfile, start, end)
        for filter in scanfilters:
            if convertPolarity[filter.Polarity] == polarity:
                return filter
        return None

    def getSpectrumPolarity(self, scanNum):
        rawScanNum = int(scanNum) + self.firstRawScanNum
        scanfilter = self.rawfile.GetFilterForScanNumber(rawScanNum)
        return convertPolarity[scanfilter.Polarity]

    def datetimeRange2ScanNumRange(self, datetimeRange: Tuple[datetime, datetime]):
        return self.timeRange2ScanNumRange((datetimeRange[0] - self.creationDatetime, datetimeRange[1] - self.creationDatetime))

    def timeRange2ScanNumRange(self, timeRange: Tuple[timedelta, timedelta]):
        s: slice = functions.binary_search.indexBetween(
            self, timeRange, (0, self.totalScanNum),
            method=(lambda _, i: self.getSpectrumRetentionTime(i)))
        return (s.start, s.stop)

    def scanNumRange2TimeRange(self, numRange: Tuple[int, int]) -> Tuple[timedelta, timedelta]:
        return self.getSpectrumRetentionTime(numRange[0]), self.getSpectrumRetentionTime(numRange[1] - 1)

    def scanNumRange2DatetimeRange(self, numRange: Tuple[int, int]):
        return self.creationDatetime + self.getSpectrumRetentionTime(numRange[0]), self.creationDatetime + self.getSpectrumRetentionTime(numRange[1])

    def checkAverageEmpty(self, timeRange: Tuple[timedelta, timedelta] = None, numRange: Tuple[int, int] = None, polarity=-1):
        if timeRange is not None and numRange is None:
            start, end = self.timeRange2ScanNumRange(timeRange)
        elif numRange is not None and timeRange is None:
            start, end = numRange
        else:
            raise ValueError(
                "`timeRange` or `numRange` must be provided and only one can be provided")

        for i in range(start, end):
            if self.getSpectrumPolarity(i) == polarity:
                return False
        return True

    def getAveragedSpectrumInTimeRange(self, start: datetime, end: datetime, rtol, polarity):
        startFloat = (start - self.creationDatetime).total_seconds() / 60
        endFloat = (end - self.creationDatetime).total_seconds() / 60
        if (scanfilter := self.getFilterInTimeRange(startFloat, endFloat, polarity)) is None:
            return
        # Due to a bug related to scan time during data acquisition, AverageScansInTimeRange should not be used
        # averaged = Extensions.AverageScansInTimeRange(self.rawfile, start, end, scanfilter, MassOptions(rtol, ToleranceUnits.ppm))
        startNum, endNum = self.datetimeRange2ScanNumRange((start, end))
        averaged = Extensions.AverageScansInScanRange(
            self.rawfile, self.getRawScanNum(startNum), self.getRawScanNum(endNum), scanfilter, MassOptions(rtol, ToleranceUnits.ppm))
        if averaged is None:
            return
        # if (averaged := Extensions.AverageScansInTimeRange(self.rawfile, start, end, scanfilter, MassOptions(rtol, ToleranceUnits.ppm))) is None:
        #    return
        averaged = averaged.SegmentedScan
        mass = np.fromiter(averaged.Positions, np.float64)
        intensity = np.fromiter(averaged.Intensities, np.float64)
        return mass, intensity

    def __del__(self):
        self.rawfile.Dispose()
