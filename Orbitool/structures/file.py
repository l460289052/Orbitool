from __future__ import annotations
from typing import Dict, Tuple, Union, Iterable, List
from datetime import datetime, timedelta

import numpy as np

from . import HDF5
from .HDF5 import datatable
from ..utils import iterator, readers
from ..functions.file import part_by_time_interval

from . import spectrum


class File(datatable.DatatableItem):
    item_name = "File"

    path = datatable.str_utf8()
    createDatetime = datatable.Datetime64s()
    startDatetime = datatable.Datetime64s()
    endDatetime = datatable.Datetime64s()


_fileReader = readers.ThermoFile


def setFileReader(fr):
    global _fileReader
    _fileReader = fr
    
def getFileReader():
    return _fileReader


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
        f = _fileReader(filepath)

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
    start_time = datatable.Datetime64s()
    end_time = datatable.Datetime64s()
    rtol = datatable.Float32()
    polarity = datatable.Int32()

    average_index = datatable.Int32()

    @staticmethod
    def generate_infos_from_paths_by_number(paths, rtol, N, polarity, timeRange) -> List[SpectrumInfo]:
        pass

    @staticmethod
    def generate_infos_from_paths_by_time_interval(paths, rtol, interval: timedelta, polarity, timeRange) -> List[SpectrumInfo]:
        files = map(_fileReader, paths)
        start_times, end_times = zip(
            *((f.startDatetime, f.endDatetime) for f in files))
        rets = part_by_time_interval(
            paths, start_times, end_times, timeRange[0], timeRange[1], interval)
        return [SpectrumInfo(path, start, end, rtol, polarity, index) for path, start, end, index in rets]

    @staticmethod
    def generate_infos_from_paths(paths, rtol, polarity, timeRange) -> List[SpectrumInfo]:
        info_list = []
        for path in paths:
            f = _fileReader(path)
            creationTime = f.creationDatetime
            for i in range(*f.timeRange2NumRange((timeRange[0] - creationTime, timeRange[1] - creationTime))):
                if f.getSpectrumPolarity(i) == polarity:
                    time = creationTime + f.getSpectrumRetentionTime(i)
                    info = SpectrumInfo(path, time, time, i,
                                        i + 1, rtol, polarity, 0)
                    info_list.append(info)
        return info_list
        
    def get_spectrum_from_info(self, reader:_fileReader = None, with_minutes = False):
        if reader is None:
            reader = _fileReader(self.file_path)
        ret = reader.getAveragedSpectrumInTimeRange(self.start_time, self.end_time, self.rtol, self.polarity)
        if ret is None:
            return None
        mz, intensity = ret
        if not with_minutes:
            return mz, intensity
        minutes = min(self.end_time, reader.endDatetime) - max(self.start_time, reader.startDatetime)
        return mz, intensity, minutes.total_seconds()/60