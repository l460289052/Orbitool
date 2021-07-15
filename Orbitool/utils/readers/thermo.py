# -*- coding: utf-8 -*-

from ... import functions

import os
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
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
    rawfile = RawFileReaderAdapter.FileFactory(path)
    rawfile.SelectInstrument(Device.MS, 1)
    rawfile.IncludeReferenceAndExceptionData = True
    return rawfile


class File:
    def __init__(self, fullname):
        self.path = fullname
        self.name = os.path.split(fullname)[1]
        self.rawfile = initRawFile(fullname)

        time = self.rawfile.FileHeader.CreationDate # time doesn't contain time zone info
        self.creationDatetime = datetime(year=time.Year, month=time.Month, day=time.Day, hour=time.Hour,
                                         minute=time.Minute, second=time.Second, microsecond=time.Millisecond * 1000)
        self.startTimedelta = timedelta(
            minutes=self.rawfile.RunHeader.StartTime)
        self.endTimedelta = timedelta(
            minutes=self.rawfile.RunHeader.EndTime)
        self.firstScanNumber = self.rawfile.RunHeader.FirstSpectrum
        self.lastScanNumber = self.rawfile.RunHeader.LastSpectrum
        self.massResolution = int(
            self.rawfile.GetTrailerExtraInformation(1).Values[11])

    @property
    def startDatetime(self):
        return self.creationDatetime + self.startTimedelta

    @property
    def endDatetime(self):
        return self.creationDatetime + self.endTimedelta

    def getSpectrumRetentionTime(self, scanNum):
        return timedelta(minutes=self.rawfile.RetentionTimeFromScanNumber(scanNum))

    def getSpectrumRetentionTimes(self):
        return [self.getSpectrumRetentionTime(scanNum) for scanNum in range(self.firstScanNumber, self.lastScanNumber + 1)]

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
        scanfilter = self.rawfile.GetFilterForScanNumber(scanNum)
        return convertPolarity[scanfilter.Polarity]

    def getSpectrum(self, scanNum):
        rawfile = self.rawfile
        retentimeTime = timedelta(
            minutes=rawfile.RetentionTimeFromScanNumber(scanNum))
        scanStatistics = rawfile.GetScanStatsForScanNumber(scanNum)
        segmentedScan = rawfile.GetSegmentedScanFromScanNumber(
            scanNum, scanStatistics)
        mz = np.array(list(segmentedScan.Positions), dtype=np.float)
        intensity = np.array(list(segmentedScan.Intensities), dtype=np.float)
        time = retentimeTime + self.creationDatetime
        # return OrbitoolBase.Spectrum(self.creationDatetime, mz, intensity, (time, time), (scanNum, scanNum))

    def datetimeRange2NumRange(self, datetimeRange: Tuple[datetime, datetime]):
        return self.timeRange2NumRange((datetimeRange[0] - self.creationDatetime, datetimeRange[1] - self.creationDatetime))

    def timeRange2NumRange(self, timeRange: Tuple[timedelta, timedelta]):
        s: slice = functions.binary_search.indexBetween(
            self, timeRange, (self.firstScanNumber, self.lastScanNumber + 1),
            method=(lambda f, i: f.getSpectrumRetentionTime(i)))
        return (s.start, s.stop)

    def numRange2TimeRange(self, numRange: Tuple[int, int]) -> Tuple[timedelta, timedelta]:
        return self.getSpectrumRetentionTime(numRange[0]), self.getSpectrumRetentionTime(numRange[1] - 1)

    def checkAverageEmpty(self, timeRange: Tuple[timedelta, timedelta] = None, numRange: Tuple[int, int] = None, polarity=-1):
        if timeRange is not None and numRange is None:
            start, end = self.timeRange2NumRange(timeRange)
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
        start = (start - self.creationDatetime).total_seconds() / 60
        end = (end - self.creationDatetime).total_seconds() / 60
        if (scanfilter := self.getFilterInTimeRange(start, end, polarity)) is None:
            return
        if (averaged := Extensions.AverageScansInTimeRange(self.rawfile, start, end, scanfilter, MassOptions(rtol, ToleranceUnits.ppm))) is None:
            return
        averaged = averaged.SegmentedScan
        mass = np.fromiter(averaged.Positions, np.float64)
        intensity = np.fromiter(averaged.Intensities, np.float64)
        return mass, intensity

    def getAveragedSpectrum(self, ppm, timeRange: Tuple[timedelta, timedelta] = None, numRange: Tuple[int, int] = None, polarity=-1):
        start, end = self.bothToNumRange(timeRange, numRange)

        scanfilter = self.getFilter(start, end, polarity)
        if scanfilter is None:
            return None

        last = end - 1
        massOption = MassOptions(ppm, ToleranceUnits.ppm)
        sTime = self.creationDatetime + self.getSpectrumRetentionTime(start)
        if start <= last:
            averaged = Extensions.AverageScansInScanRange(
                self.rawfile, start, last, scanfilter, massOption)
            if averaged is None:  # I don't know why it could be a None
                return None
            mz, intensity, eTime = self.parseSpectrum(averaged, last)
        else:
            return None

        timeRange = (sTime, eTime)

        numRange = (start, end)
        return mz, intensity

    def bothToNumRange(self, timeRange: Tuple[timedelta, timedelta], numRange: Tuple[int, int]) -> Tuple[int, int]:
        if timeRange is not None and numRange is None:
            return self.timeRange2NumRange(timeRange)
        elif numRange is not None and timeRange is None:
            return numRange
        else:
            raise ValueError(
                "`timeRange` or `numRange` must be provided and only one can be provided")

    def parseSpectrum(self, averaged, last):
        averaged = averaged.SegmentedScan
        mz = np.array(list(averaged.Positions), dtype=np.float)
        intensity = np.array(list(averaged.Intensities), dtype=np.float)
        eTime = self.creationDatetime + self.getSpectrumRetentionTime(last)

        return mz, intensity, eTime

    def __del__(self):
        self.rawfile.Dispose()
