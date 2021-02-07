from __future__ import annotations
from typing import Dict, Tuple, Union, Iterable, List
from datetime import datetime, timedelta

import numpy as np

from Orbitool.structures import HDF5
from Orbitool.structures.HDF5 import datatable
from Orbitool.utils import iterator, readers

from . import spectrum


class File(datatable.DatatableItem):
    item_name = "File"

    path = datatable.str_utf8()
    createDatetime = datatable.Datetime64s()
    startDatetime = datatable.Datetime64s()
    endDatetime = datatable.Datetime64s()


fileReader = readers.ThermoFile


def setFileReader(fr):
    global fileReader
    fileReader = fr


class FileList(HDF5.Group):
    h5_type = HDF5.RegisterType("FileList")
    files: datatable.Datatable = datatable.Datatable.descriptor(File)

    def _crossed(self, start: datetime, end: datetime) -> Tuple[bool, str]:
        startDatetimes = self.files.get_column("startDatetime")
        endDatetimes = self.files.get_column("endDatetime")
        slt = (start < startDatetimes) & (endDatetimes < end)
        where = np.where(slt)
        if len(where) > 0:
            return False, list(self.files[where])
        return True, None

    @property
    def timeRange(self):
        if len(self.files) == 0:
            return None, None
        startDatetimes = self.files.get_column("startDatetime")
        endDatetimes = self.files.get_column("endDatetime")
        return startDatetimes.min().astype(datetime), endDatetimes.max().astype(datetime)

    def addFile(self, filepath):
        f = fileReader(filepath)

        crossed, crossedFiles = self._crossed(f.startDatetime, f.endDatetime)
        if crossed:
            raise ValueError(
                f'file "{f.path}" and "{[f.path for f in crossedFiles]}" have crossed scan time')

        file = File(f.path, f.creationDatetime, f.creationDatetime +
                    f.startTimedelta, f.creationDatetime + f.endTimedelta)
        self.files.extend([file])

    def rmFile(self, indexes: Union[int, Iterable[int]]):
        if isinstance(indexes, int):
            indexes = (indexes, )
        del self.files[np.array(indexes)]

    def sort(self):
        self.files.sort("createDatetime")

    def clear(self):
        self.files.clear()
        self.initialize()

    def __iter__(self):
        return iter(self.files)

    def __len__(self):
        return len(self.files)


class SpectrumInfo(datatable.DatatableItem):
    item_name = "SpectrumInfo"

    file_path = datatable.str_utf8()
    startTime = datatable.Datetime64s()
    endTime = datatable.Datetime64s()
    startIndex = datatable.Int32()
    endIndex = datatable.Int32()
    rtol = datatable.Float32()
    polarity = datatable.Int32()
    
    average_index = datatable.Int32()

    @staticmethod
    def generate_infos_from_paths_by_number(paths, rtol, N, polarity, timeRange) -> List[SpectrumInfo]:
        pass

    @staticmethod
    def generate_infos_from_paths_by_time_interval(paths, rtol, interval: timedelta, polarity, timeRange) -> List[SpectrumInfo]:
        info_list = []
        files = iterator(map(fileReader, paths))

        startTime, endTime = timeRange
        start = startTime
        f = files.value
        while not files.end and f.endDatetime < start:
            files.next()
            f = files.value
        if files.end:
            return info_list

        end = start + interval
        if end > endTime:
            end = endTime
        f_create = f.creationDatetime
        f_start = f.startDatetime
        f_end = f.endDatetime
        while start <= endTime and not files.end:
            if f_end >= end:
                if f_start > end:
                    start += int((f_start - start) / interval) * interval
                    end = start + interval
                    if start > endTime:
                        break
                    if end > endTime:
                        end = endTime
                r = f.timeRange2NumRange((start - f_create, end - f_create))
                if not f.checkAverageEmpty((start - f_create, end - f_create)):
                    info_list.append(SpectrumInfo(
                        f.path, start, end, r[0], r[1], rtol, polarity, 0))
                if f_end == end:
                    files.next()
                    f = files.value
                    f_create = f.creationDatetime
                    f_start = f.startDatetime
                    f_end = f.endDatetime
            else:
                average_index = 0
                while True:
                    if f_start > end:
                        break
                    r = f.timeRange2NumpyRange((start-f_create, end-f_create))
                    info_list.append(SpectrumInfo(f.path, start, end, r[0], r[1], rtol, polarity, average_index))
                    files.next()
                    if files.end:
                        break
                    f = files.value
                    f_create = f.creationDatetime
                    f_start = f.startDatetime
                    f_end = f.endDatetime

            start += interval
            end = start + interval
            if end > endTime:
                end = endTime
        return info_list

    @staticmethod
    def generate_infos_from_paths(paths, rtol, polarity, timeRange) -> List[SpectrumInfo]:
        info_list = []
        for path in paths:
            f = fileReader(path)
            creationTime = f.creationDatetime
            for i in range(*f.timeRange2NumRange((timeRange[0] - creationTime, timeRange[1] - creationTime))):
                if f.getSpectrumPolarity(i) == polarity:
                    time = creationTime + f.getSpectrumRetentionTime(i)
                    info = SpectrumInfo(path, time, time, i,
                                        i + 1, rtol, polarity, 0)
                    info_list.append(info)
        return info_list

    def get_spectrum(self, spectrum: spectrum.Spectrum):
        if len(self.file_path.split('|')) > 1:
            pass
        else:
            mz, intensity = fileReader(self.file_path).getAveragedSpectrum(
                self.rtol, numRange=(self.startIndex, self.endIndex), polarity=self.polarity)
            spectrum.startTime = self.startTime
            spectrum.endTime = self.endTime
            spectrum.file_path = self.file_path
            spectrum.mz = mz
            spectrum.intensity = intensity
