from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple, Union

import numpy as np

from ..functions.file import part_by_time_interval
from ..utils.readers import ThermoFile
from . import spectrum
from .base import BaseStructure, BaseRowItem, Field


class Path(BaseRowItem):
    item_name = "Path"

    path: str
    createDatetime: datetime
    startDatetime: datetime
    endDatetime: datetime


PATH_THERMOFILE = "Thermo"
PATH_HDF5 = "HDF5"


class PathList(BaseStructure):
    h5_type = "PathList"
    paths: List[Path] = Field(default_factory=list)

    def _crossed(self, start: datetime, end: datetime) -> Tuple[bool, str]:
        for path in self.paths:
            if start < path.startDatetime and path.endDatetime < end:
                return True, path.path
        return False, None

    @property
    def timeRange(self):
        if not self.paths:
            return None, None
        it = iter(self.paths)
        f = next(it)
        start, end = f.startDatetime, f.endDatetime
        for f in it:
            if f.startDatetime < start:
                start = f.startDatetime
            if f.endDatetime > end:
                end = f.endDatetime
        return start, end

    def addThermoFile(self, filepath):
        f = ThermoFile(filepath)

        crossed, crossed_file = self._crossed(f.startDatetime, f.endDatetime)
        if crossed:
            raise ValueError(
                f'file "{f.path}" and "{crossed_file}" have crossed scan time')

        path = Path(path=f"{PATH_THERMOFILE}:{f.path}", createDatetime=f.creationDatetime, startDatetime=f.creationDatetime +
                    f.startTimedelta, endDatetime=f.creationDatetime + f.endTimedelta)
        self.paths.append(path)

    def addCsv(self, *args):
        path = Path(path=f"h5:{path}")

    def _addPath(self, p: Path):
        self.paths.append(p)

    def rmPath(self, indexes: Union[int, Iterable[int]]):
        if isinstance(indexes, int):
            indexes = (indexes, )
        indexes = np.unique(indexes)[::-1]
        for index in indexes:
            del self.paths[index]

    def subList(self, indexes: Union[int, Iterable[int]]) -> PathList:
        if isinstance(indexes, int):
            indexes = (indexes,)
        indexes = np.unique(indexes)
        sub_list = PathList()
        for index in indexes:
            sub_list._addPath(self.paths[index])
        return sub_list

    def sort(self):
        self.paths.sort(key=lambda f: f.createDatetime)

    def clear(self):
        self.paths.clear()

    def __iter__(self):
        return iter(self.paths)

    def __len__(self):
        return len(self.paths)


class FileSpectrumInfo(spectrum.SpectrumInfo):
    item_name = "file spectrum info"

    path: str  # "type:path"
    polarity: int

    average_index: int

    @classmethod
    def spectrum_iter(cls, paths: List[Path], polarity, timeRange):
        for path in paths:
            origin, realpath = path.path.split(':', 1)
            if origin == PATH_THERMOFILE:
                f = ThermoFile(realpath)
                index_range = f.datetimeRange2NumRange(timeRange)
                for scan_num in range(*index_range):
                    if polarity == f.getSpectrumPolarity(scan_num):
                        yield path.path, f.getSpectrumDatetime(scan_num)

    @classmethod
    def generate_infos_from_paths_by_number(cls, paths: List[Path], N: int, polarity, timeRange):
        delta_time = timedelta(seconds=1)

        results: List[cls] = []
        left_index = N
        average_index = 0
        former_path = ""
        info: cls = None
        for path, time in cls.spectrum_iter(paths, polarity, timeRange):
            if former_path == path and left_index:
                info.end_time = time + delta_time
            else:
                if not left_index:
                    average_index = 0
                info = cls(start_time=time - delta_time, end_time=time + delta_time, path=path,
                           polarity=polarity, average_index=average_index)
                results.append(info)
                average_index += 1
                former_path = path
            if left_index:
                left_index -= 1
            else:
                left_index = N - 1
        return results

    @classmethod
    def generate_infos_from_paths_by_time_interval(cls, paths: List[Path], interval: timedelta, polarity, timeRange):
        start_times, end_times = zip(
            *((p.startDatetime, p.endDatetime) for p in paths))
        paths_str = [path.path for path in paths]
        rets = part_by_time_interval(
            paths_str, start_times, end_times, timeRange[0], timeRange[1], interval)
        ret = [cls(
            path=path, start_time=start, end_time=end, polarity=polarity,
            average_index=index) for path, start, end, index in rets]
        return ret

    @classmethod
    def generate_infos_from_paths(cls, paths: List[Path], polarity, timeRange):
        delta_time = timedelta(seconds=1)
        info_list: List[cls] = []
        for path in paths:
            origin, realpath = path.path.split(':', 1)
            if origin == PATH_THERMOFILE:
                f = ThermoFile(realpath)
                creationTime = f.creationDatetime
                for i in range(*f.timeRange2NumRange((timeRange[0] - creationTime, timeRange[1] - creationTime))):
                    if f.getSpectrumPolarity(i) == polarity:
                        time = creationTime + f.getSpectrumRetentionTime(i)
                        info = FileSpectrumInfo(path=path.path, start_time=time - delta_time, end_time=time + delta_time,
                                                polarity=polarity, average_index=0)
                        info_list.append(info)
        return info_list

    def get_spectrum_from_info(self, rtol: float = 1e-6, with_minutes=False):
        origin, realpath = self.path.split(':', 1)
        if origin == PATH_THERMOFILE:
            reader = ThermoFile(realpath)
            ret = reader.getAveragedSpectrumInTimeRange(
                self.start_time, self.end_time, rtol, self.polarity)
            if ret is None:
                return None
            mz, intensity = ret
            if not with_minutes:
                return mz, intensity
            minutes = min(self.end_time, reader.endDatetime) - \
                max(self.start_time, reader.startDatetime)
            return mz, intensity, minutes.total_seconds() / 60
