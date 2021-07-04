from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple, Union

import numpy as np

from ..functions.file import part_by_time_interval
from ..utils.readers import ThermoFile
from . import spectrum
from .base import BaseStructure, BaseTableItem, Field


class Path(BaseTableItem):
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
    rtol: int
    polarity: int

    average_index: int

    @staticmethod
    def generate_infos_from_paths_by_number(paths, rtol, N, polarity, timeRange) -> List[FileSpectrumInfo]:
        pass

    @staticmethod
    def generate_infos_from_paths_by_time_interval(paths: List[Path], rtol, interval: timedelta, polarity, timeRange) -> List[FileSpectrumInfo]:
        start_times, end_times = zip(
            *((p.startDatetime, p.endDatetime) for p in paths))
        paths_str = [path.path for path in paths]
        rets = part_by_time_interval(
            paths_str, start_times, end_times, timeRange[0], timeRange[1], interval)
        ret = [FileSpectrumInfo(
            path=path, start_time=start, end_time=end, rtol=rtol, polarity=polarity,
            average_index=index) for path, start, end, index in rets]
        return ret

    @staticmethod
    def generate_infos_from_paths(paths: List[Path], rtol, polarity, timeRange) -> List[FileSpectrumInfo]:
        info_list = []
        for path in paths:
            origin, realpath = path.path.split(':', 1)
            if origin == PATH_THERMOFILE:
                f = ThermoFile(realpath)
                creationTime = f.creationDatetime
                for i in range(*f.timeRange2NumRange((timeRange[0] - creationTime, timeRange[1] - creationTime))):
                    if f.getSpectrumPolarity(i) == polarity:
                        time = creationTime + f.getSpectrumRetentionTime(i)
                        info = FileSpectrumInfo(path=path.path, start_time=time, end_time=time,
                                            rtol=rtol, polarity=polarity, average_index=0)
                        info_list.append(info)
        return info_list

    def get_spectrum_from_info(self, with_minutes=False):
        origin, realpath = self.path.split(':', 1)
        if origin == PATH_THERMOFILE:
            reader = ThermoFile(realpath)
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
