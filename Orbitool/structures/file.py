from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple, Union

import numpy as np

from ..functions.file import part_by_time_interval
from ..utils import iterator, readers
from . import spectrum
from .base import BaseStructure, BaseTableItem, Field


class File(BaseTableItem):
    item_name = "File"

    path: str
    createDatetime: datetime
    startDatetime: datetime
    endDatetime: datetime


_fileReader = readers.ThermoFile


def setFileReader(fr):
    global _fileReader
    _fileReader = fr


def getFileReader():
    return _fileReader


class FileList(BaseStructure):
    h5_type = "FileList"
    files: List[File] = Field(default_factory=list)

    def _crossed(self, start: datetime, end: datetime) -> Tuple[bool, str]:
        for file in self.files:
            if start < file.startDatetime and file.endDatetime < end:
                return True, file.path
        return False, None

    @property
    def timeRange(self):
        if not self.files:
            return None, None
        it = iter(self.files)
        f = next(it)
        start, end = f.startDatetime, f.endDatetime
        for f in it:
            if f.startDatetime < start:
                start = f.startDatetime
            if f.endDatetime > end:
                end = f.endDatetime
        return start, end

    def addFile(self, filepath):
        f = _fileReader(filepath)

        crossed, crossed_file = self._crossed(f.startDatetime, f.endDatetime)
        if crossed:
            raise ValueError(
                f'file "{f.path}" and "{crossed_file}" have crossed scan time')

        file = File(path=f.path, createDatetime=f.creationDatetime, startDatetime=f.creationDatetime +
                    f.startTimedelta, endDatetime=f.creationDatetime + f.endTimedelta)
        self.files.append(file)

    def _addFile(self, f: File):
        self.files.append(f)

    def rmFile(self, indexes: Union[int, Iterable[int]]):
        if isinstance(indexes, int):
            indexes = (indexes, )
        indexes = np.unique(indexes)[::-1]
        for index in indexes:
            del self.files[index]

    def subList(self, indexes: Union[int, Iterable[int]]):
        if isinstance(indexes, int):
            indexes = (indexes,)
        indexes = np.unique(indexes)
        subList = FileList()
        for index in indexes:
            subList._addFile(self.files[index])

    def sort(self):
        self.files.sort(key=lambda f: f.createDatetime)

    def clear(self):
        self.files.clear()

    def __iter__(self):
        return iter(self.files)

    def __len__(self):
        return len(self.files)


class SpectrumInfo(BaseTableItem):
    item_name = "SpectrumInfo"

    file_path: str
    start_time: datetime
    end_time: datetime
    rtol: int
    polarity: int

    average_index: int

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
        ret = [SpectrumInfo(
            file_path=path, start_time=start, end_time=end, rtol=rtol, polarity=polarity,
            average_index=index) for path, start, end, index in rets]
        return ret

    @staticmethod
    def generate_infos_from_paths(paths, rtol, polarity, timeRange) -> List[SpectrumInfo]:
        info_list = []
        for path in paths:
            f = _fileReader(path)
            creationTime = f.creationDatetime
            for i in range(*f.timeRange2NumRange((timeRange[0] - creationTime, timeRange[1] - creationTime))):
                if f.getSpectrumPolarity(i) == polarity:
                    time = creationTime + f.getSpectrumRetentionTime(i)
                    info = SpectrumInfo(file_path=path, start_time=time, end_time=time,
                                        rtol=rtol, polarity=polarity, average_index=0)
                    info_list.append(info)
        return info_list

    def get_spectrum_from_info(self, reader: _fileReader = None, with_minutes=False):
        if reader is None:
            reader = _fileReader(self.file_path)
        ret = reader.getAveragedSpectrumInTimeRange(
            self.start_time, self.end_time, self.rtol, self.polarity)
        if ret is None:
            return None
        mz, intensity = ret
        if not with_minutes:
            return mz, intensity
        minutes = min(self.end_time, reader.endDatetime) - \
            max(self.start_time, reader.startDatetime)
        return mz, intensity, minutes.total_seconds() / 60
