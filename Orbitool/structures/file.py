from datetime import datetime, timedelta
import math
from typing import Dict, Iterable, List, Tuple, Union

import numpy as np

from ..functions.file import (
     part_by_periods, generage_periods, 
     generate_num_periods)
from ..utils.readers import ThermoFile
from . import spectrum
from .base import field
from .base_structure import BaseStructure
from .base_row import BaseRowItem
from .HDF5 import Row


class Path(BaseRowItem):
    item_name = "Path"

    path: str
    createDatetime: datetime
    startDatetime: datetime
    endDatetime: datetime
    scanNum: int = 0

    def getFileHandler(self):
        typ, path = self.path.split(":", 1)
        match typ:
            case PATH_THERMOFILE:
                return ThermoFile(path)

    @classmethod
    def fromThermoFile(cls, filepath):
        handler = ThermoFile(filepath)
        return cls(
            f"{PATH_THERMOFILE}:{filepath}",
            handler.creationDatetime, handler.startDatetime,
            handler.endDatetime, handler.totalScanNum)


PATH_THERMOFILE = "Thermo"
PATH_HDF5 = "HDF5"


class PathList(BaseStructure):
    h5_type = "PathList"
    paths: Row[Path] = field(list)

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
        path = Path.fromThermoFile(filepath)

        crossed, crossed_file = self._crossed(path.startDatetime, path.endDatetime)
        if crossed:
            raise ValueError(
                f'file "{filepath}" and "{crossed_file}" have crossed scan time')

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

    def subList(self, indexes: Union[int, Iterable[int]]):
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


class PeriodItem(BaseRowItem):
    item_name = "spectrum period item"
    start_time: datetime = None
    end_time: datetime = None
    start_num: int = -1
    end_num: int = -1

    def length(self):
        return self.start_time and (self.end_time - self.start_time) or (self.end_num - self.start_num)
        


class FileSpectrumInfo(spectrum.SpectrumInfo):
    item_name = "file spectrum info"

    path: str  # "type:path"
    polarity: int

    # index from 0, 1, 2, 3... with different times together to make up a whole spectrum
    average_index: int

    @classmethod
    def infosFromNumInterval(cls, paths: List[Path], N: int, polarity, timeRange):
        scan_num_sum = 0
        start_scan_num = -1
        stop_scan_num = -1
        for path in paths:
            handler = path.getFileHandler()
            start, stop = handler.datetimeRange2ScanNumRange(timeRange)
            if start < stop:
                if start_scan_num < 0:
                    start_scan_num = scan_num_sum + start
                stop_scan_num = scan_num_sum + stop
            scan_num_sum += handler.totalScanNum
        periods = generate_num_periods(start_scan_num, stop_scan_num, N) 
        return cls.infosFromNumPeriods(paths, polarity, periods)

    @classmethod
    def infosFromNumPeriods(cls, paths: List[Path], polarity, periods: List[Tuple[int, int]]):
        delta_time = timedelta(seconds=1)

        results: List[cls] = []

        scan_num_sum = 0

        i = 0
        start, end = periods[i]
        average_index = 0
        for path in paths:
            handler = path.getFileHandler()
            if scan_num_sum <= start < scan_num_sum + handler.totalScanNum:
                time_range = handler.scanNumRange2TimeRange((start-scan_num_sum, end-scan_num_sum))
                info = cls(
                    start_time=time_range[0] - delta_time,
                    end_time=time_range[1] + delta_time,
                    path=path.path,
                    polarity=polarity,
                    average_index=average_index)
                results.append(info)
                if end < scan_num_sum + handler.totalScanNum:
                    average_index = 0
                    i += 1
                    if len(periods) >= i:
                        break
                    start, end = periods[i]
                else:
                    average_index += 1
                    start = scan_num_sum + handler.totalScanNum
                scan_num_sum += handler.totalScanNum

        return results

    @classmethod
    def infosFromTimeInterval(cls, paths: List[Path], interval: timedelta, polarity, timeRange):
        periods = generage_periods(timeRange[0], timeRange[1], interval)
        return cls.infosFromPeriods(paths, polarity, periods)

    @classmethod
    def infosFromPeriods(cls, paths: List[Path], polarity, periods: Iterable[Tuple[datetime, datetime]]):
        start_times, end_times = zip(
            *((p.startDatetime, p.endDatetime) for p in paths))
        paths_str = [path.path for path in paths]
        rets = part_by_periods(paths_str, start_times, end_times, periods)
        ret = [cls(
            path=path, start_time=start, end_time=end, polarity=polarity,
            average_index=index) for path, start, end, index in rets]
        return ret

    @classmethod
    def infosFromPath_withoutAveraging(cls, paths: List[Path], polarity, timeRange):
        delta_time = timedelta(seconds=1)
        info_list: List[cls] = []
        for path in paths:
            handler = path.getFileHandler()
            creationTime = handler.creationDatetime
            for i in range(*handler.timeRange2ScanNumRange((timeRange[0] - creationTime, timeRange[1] - creationTime))):
                if handler.getSpectrumPolarity(i) == polarity:
                    time = creationTime + handler.getSpectrumRetentionTime(i)
                    info = FileSpectrumInfo(
                        time - delta_time, time + delta_time, path.path, polarity, 0)
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
