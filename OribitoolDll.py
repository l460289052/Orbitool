# -*- coding: utf-8 -*-

import OribitoolBase
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

from ThermoFisher.CommonCore.Data import ToleranceUnits, Extensions
from ThermoFisher.CommonCore.Data.Business import ChromatogramSignal, ChromatogramTraceSettings, \
     DataUnits, Device, GenericDataTypes, SampleType, Scan, TraceType, MassOptions
from ThermoFisher.CommonCore.Data.FilterEnums import IonizationModeType, MSOrderType, PolarityType
from ThermoFisher.CommonCore.Data.Interfaces import IChromatogramSettings, IScanEventBase, \
     IScanFilter, RawFileClassification
from ThermoFisher.CommonCore.MassPrecisionEstimator import PrecisionEstimate
from ThermoFisher.CommonCore.RawFileReader import RawFileReaderAdapter

convertPolarity = {PolarityType.Any: 0,
                   PolarityType.Positive: 1,
                   PolarityType.Negative: -1}

class File:
    def __init__(self, fullname):
        rawfile = RawFileReaderAdapter.FileFactory(fullname)
        rawfile.SelectInstrument(Device.MS, 1)
        rawfile.IncludeReferenceAndExceptionData = True
        self.path = fullname
        self.name = os.path.split(fullname)[1]
        self.rawfile = rawfile
        time = self.rawfile.FileHeader.CreationDate
        self.creationDate = datetime.datetime(year=time.Year, month=time.Month, day=time.Day, hour=time.Hour,
                              minute=time.Minute, second=time.Second, microsecond=time.Millisecond*1000)
        self.startTime = datetime.timedelta(minutes=self.rawfile.RunHeader.StartTime)
        self.endTime = datetime.timedelta(minutes=self.rawfile.RunHeader.EndTime)
        self.firstScanNumber = self.rawfile.RunHeader.FirstSpectrum
        self.lastScanNumber = self.rawfile.RunHeader.LastSpectrum
        self.massResolution = int(self.rawfile.GetTrailerExtraInformation(1).Values[11])
        
    def getSpectrumRetentionTime(self, scanNum):
        return datetime.timedelta(minutes=self.rawfile.RetentionTimeFromScanNumber(scanNum))
    
    def getSpectrumRetentionTimes(self):
        return [self.getSpectrumRetentionTime(scanNum) for scanNum in range(self.firstScanNumber, self.lastScanNumber + 1)]
        
    def getFilter(self, polarity):
        scanfilter = None
        filters = self.rawfile.GetFilters()
        for f in filters:
            if convertPolarity[f.Polarity] == polarity:
                scanfilter = f
        return scanfilter

    def getSpectrumPolarity(self, scanNum):
        scanfilter = self.rawfile.GetFilterForScanNumber(scanNum)
        return convertPolarity[scanfilter.Polarity]

    def getSpectrum(self, scanNum):
        rawfile = self.rawfile
        retentimeTime = datetime.timedelta(minutes=rawfile.RetentionTimeFromScanNumber(scanNum))
        scanStatistics = rawfile.GetScanStatsForScanNumber(scanNum)
        segmentedScan = rawfile.GetSegmentedScanFromScanNumber(
            scanNum, scanStatistics)
        mz = np.array(list(segmentedScan.Positions), dtype=np.float)
        intensity = np.array(list(segmentedScan.Intensities), dtype=np.float)
        time = retentimeTime+self.creationDate
        return OribitoolBase.Spectrum(self.creationDate, mz, intensity, (time, time), (scanNum, scanNum))
        
    def getAveragedSpectrum(self, ppm, timeRange: Tuple[datetime.timedelta, datetime.timedelta] = None, numRange: Tuple[int, int] = None, polarity = -1):
        averaged = None

        rawfile = self.rawfile
        def method(f, index: int) -> datetime.timedelta:
            return f.getSpectrumRetentionTime(index)

        start = None
        end = None
        if timeRange is not None and numRange is None:
            r: range = OribitoolFunc.indexBetween(self, timeRange,
                                                    (self.firstScanNumber,
                                                    self.lastScanNumber + 1),
                                                    method=method)
            start = r.start
            end = r.stop
        elif numRange is not None and timeRange is None:
            start, end = numRange
        else:
            raise ValueError(
                "`timeRange` or `numRange` must be provided and only one can be provided")
        scanfilter = self.getFilter(polarity)
        last = end - 1
        massOption = MassOptions(ppm, ToleranceUnits.ppm)
        if start<=last:
            averaged = Extensions.AverageScansInScanRange(
                rawfile, start, last, scanfilter, massOption).SegmentedScan
            mz = np.array(list(averaged.Positions), dtype=np.float)
            intensity = np.array(list(averaged.Intensities), dtype=np.float)
        else:
            mz = np.zeros(0, dtype=np.float)
            intensity = np.zeros(0, dtype=np.float)

        sTime = self.creationDate +  self.getSpectrumRetentionTime(start)
        eTime = self.creationDate + self.getSpectrumRetentionTime(last)

        timeRange = (sTime, eTime)

        numRange = (start,end)
        return OribitoolBase.Spectrum(self.creationDate, mz, intensity, timeRange, numRange)

    def __del__(self):
        self.rawfile.Dispose()
