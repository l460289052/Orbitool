# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from functools import cached_property
from typing import Dict, List, Tuple, Counter, Any
import os

import numpy as np
from Orbitool import setting

from ..binary_search import indexBetween
from .spectrum_filter import SpectrumFilter
from . import spectrum_filter

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
        return [self.getSpectrumRetentionTime(scan_num) for scan_num in range(self.totalScanNum)]

    def getSpectrumDatetime(self, scanNum):
        return self.creationDatetime + self.getSpectrumRetentionTime(scanNum)

    def checkFilter(self, polarity) -> bool:
        for f in self.rawfile.GetFilters():
            if convertPolarity[f.Polarity] == polarity:
                return True
        return False

    def getFilterList(self, num_range: Tuple[int, int] = None, time_range: Tuple[datetime, datetime] = None, *, raw_num_range: Tuple[int, int] = None):
        if raw_num_range is None:
            if num_range is None:
                if time_range is None:
                    num_range = (0, self.totalScanNum)
                else:
                    num_range = self.datetimeRange2ScanNumRange(time_range)
            raw_num_range = (self.getRawScanNum(
                num_range[0]), self.getRawScanNum(num_range[1]))

        f = self.rawfile
        filters = f.GetFilters()
        if len(filters) == 1:
            filter = ToSpectrumFilter(filters[0])
            for i in range(*raw_num_range):
                yield filter
        else:
            for i in range(*raw_num_range):
                yield ToSpectrumFilter(f.GetFilterForScanNumber(i))

    def getUniqueFilters(self):
        return list(map(ToSpectrumFilter, self.rawfile.GetFilters()))

    def _getMostFilterInRawNumRange(self, start: int, stop: int, target_filter: SpectrumFilter):
        f = self.rawfile
        filters = f.GetFilters()
        if len(filters) == 1:
            rawfilter = filters[0]
            filter = ToSpectrumFilter(rawfilter)
            return rawfilter if spectrum_filter.match(filter, target_filter) else None


        counter = Counter[str]()
        raw_map: Dict[str, Any] = {}
        for i in range(start, stop):
            rawfilter = f.GetFilterForScanNumber(i)
            filter = ToSpectrumFilter(rawfilter)
            if spectrum_filter.match(filter, target_filter):
                counter[filter["string"]] += 1
                raw_map.setdefault(filter["string"], rawfilter)
        if not counter:
            return None
        string = counter.most_common(1)[0][0]
        return raw_map[string]

    def getSpectrumFilter(self, scan_num):
        rawScanNum = self.getRawScanNum(scan_num)
        scanfilter = self.rawfile.GetFilterForScanNumber(rawScanNum)
        return ToSpectrumFilter(scanfilter)

    def datetimeRange2ScanNumRange(self, datetimeRange: Tuple[datetime, datetime]):
        """
            return start (inclusive), stop (exclusive)
        """
        return self.timeRange2ScanNumRange((datetimeRange[0] - self.creationDatetime, datetimeRange[1] - self.creationDatetime))

    def timeRange2ScanNumRange(self, timeRange: Tuple[timedelta, timedelta]):
        """
            return start (inclusive), end (exclusive)
        """
        s: slice = indexBetween(
            self, timeRange, (0, self.totalScanNum),
            method=(lambda _, i: self.getSpectrumRetentionTime(i)))
        return (s.start, s.stop)

    def scanNumRange2TimeRange(self, numRange: Tuple[int, int]) -> Tuple[timedelta, timedelta]:
        return self.getSpectrumRetentionTime(numRange[0]), self.getSpectrumRetentionTime(numRange[1] - 1)

    def scanNumRange2DatetimeRange(self, numRange: Tuple[int, int]):
        return self.creationDatetime + self.getSpectrumRetentionTime(numRange[0]), self.creationDatetime + self.getSpectrumRetentionTime(numRange[1])

    def checkAverageEmpty(self, filter: SpectrumFilter, timeRange: Tuple[timedelta, timedelta] = None, numRange: Tuple[int, int] = None):
        if timeRange is not None and numRange is None:
            start, end = self.timeRange2ScanNumRange(timeRange)
        elif numRange is not None and timeRange is None:
            start, end = numRange
        else:
            raise ValueError(
                "`timeRange` or `numRange` must be provided and only one can be provided")

        for i in range(start, end):
            if spectrum_filter.match(self.getSpectrumFilter(i), filter):
                return False
        return True

    def getAveragedSpectrumInTimeRange(self, start: datetime, end: datetime, rtol, filter: SpectrumFilter):
        # Due to a bug related to scan time during data acquisition, AverageScansInTimeRange should not be used
        # averaged = Extensions.AverageScansInTimeRange(self.rawfile, start, end, scanfilter, MassOptions(rtol, ToleranceUnits.ppm))
        startNum, stopNum = list(
            map(self.getRawScanNum, self.datetimeRange2ScanNumRange((start, end))))
        if (scanfilter := self._getMostFilterInRawNumRange(startNum, stopNum, filter)) is None:
            return
        averaged = Extensions.AverageScansInScanRange(
            self.rawfile, startNum, stopNum-1, scanfilter, MassOptions(rtol, ToleranceUnits.ppm))
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


def ToSpectrumFilter(rawfilter) -> SpectrumFilter:
    r = rawfilter.GetMassRange(0)
    return dict(
        string=rawfilter.ToString(),
        polarity=str(convertPolarity[rawfilter.Polarity]),
        mass_range=f"{r.Low:.1f}-{r.High:.1f}",
        higher_energy_CiD="off" if rawfilter.HigherEnergyCiD.ToString(
        ) == "Off" else format(rawfilter.HigherEnergyCiDValue, ".2f"),
        scan=f"{rawfilter.ScanMode.ToString()} {rawfilter.ScanData.ToString()}"
    )


convertPolarity = {PolarityType.Any: 0,
                   PolarityType.Positive: 1,
                   PolarityType.Negative: -1}
