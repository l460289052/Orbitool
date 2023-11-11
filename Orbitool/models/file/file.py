from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path as FilePath
import random
from typing import Dict, Iterable, List, Tuple, Union

import numpy as np

from Orbitool.base import BaseRowStructure, BaseDatasetStructure, BaseStructure, JSONObject
from Orbitool.utils.readers import ThermoFile

from ..spectrum import spectrum
from .part_file import (generate_periods, generate_num_periods,
                        get_num_range_from_ranges)


class PATH_TYPE(str, Enum):
    THERMO = "Thermo"
    HDF5 = "HDF5"


class Path(BaseRowStructure):
    path: str
    key: str
    createDatetime: datetime
    startDatetime: datetime
    endDatetime: datetime
    scanNum: int = -1

    def getFileHandler(self):
        typ, path = self.path.split(":", 1)
        match typ:
            case PATH_TYPE.THERMO.value:
                return ThermoFile(path)

    @classmethod
    def fromThermoFile(cls, filepath, other_paths: Iterable["Path"]):
        handler = ThermoFile(filepath)
        stem = FilePath(filepath).stem
        key = stem
        other_keys = set(p.key for p in other_paths)
        while True:
            if key not in other_keys:
                break
            key = f"{stem}-{random.randbytes(4).hex()}"
        return cls(
            path=f"{PATH_TYPE.THERMO.value}:{filepath}",
            key=key,
            createDatetime=handler.creationDatetime,
            startDatetime=handler.startDatetime,
            endDatetime=handler.endDatetime,
            scanNum=handler.totalScanNum
        )

    def get_show_name(self):
        typ, path = self.path.split(":", 1)
        match typ:
            case PATH_TYPE.THERMO.value:
                return FilePath(path).stem


class PathList(BaseStructure):
    paths: List[Path] = []

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
        path = Path.fromThermoFile(filepath, self.paths)

        crossed, crossed_file = self._crossed(
            path.startDatetime, path.endDatetime)
        if crossed:
            raise ValueError(
                f'file "{filepath}" and "{crossed_file}" have crossed scan time')

        self.paths.append(path)
        return path

    def addCsv(self, *args):
        path = Path(path=f"h5:{path}")

    def _addPath(self, p: Path):
        self.paths.append(p)

    def rmPath(self, indexes: Union[int, Iterable[int]]):
        if isinstance(indexes, int):
            indexes = (indexes, )
        indexes = np.unique(indexes)[::-1]
        return list(map(self.paths.pop, indexes))

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


base_dt = datetime(1, 1, 1)


class PeriodItem(BaseRowStructure):
    start_time: datetime = base_dt
    end_time: datetime = base_dt
    start_num: int = -1
    stop_num: int = -1

    def use_time(self):
        return self.start_num == -1

    def length(self):
        return self.use_time() and (self.end_time - self.start_time) or (self.stop_num - self.start_num)


class FileSpectrumInfo(spectrum.SpectrumInfo):
    path: str
    filter: JSONObject

    # index from 0, 1, 2, 3... with different times together to make up a whole spectrum
    average_index: int

    @classmethod
    def infosFromNumInterval(cls, paths: List[Path], N: int, filters, timeRange):
        start_scan_num, stop_scan_num, total_scan_num = get_num_range_from_ranges(
            (p.getFileHandler() for p in paths), timeRange)
        periods = [PeriodItem(
            start_num=int(s), stop_num=int(e)
        ) for s, e in generate_num_periods(start_scan_num, stop_scan_num, N)]
        return cls.infosFromPeriods(paths, filters, periods)

    @classmethod
    def infosFromTimeInterval(cls, paths: List[Path], interval: timedelta, filters, timeRange):
        periods = [PeriodItem(
            start_time=s, end_time=e
        ) for s, e in generate_periods(timeRange[0], timeRange[1], interval)]
        return cls.infosFromPeriods(paths, filters, periods)

    @classmethod
    def infosFromPeriods(cls, paths: List[Path], polarity, periods: List[PeriodItem]):
        delta_time = timedelta(seconds=1)

        results: List[cls] = []

        scan_num_sum = 0

        i = 0
        period = periods[i]
        average_index = 0

        generate_flag = False
        next_period_flag = False
        next_file_flag = False

        for path in paths:
            handler = path.getFileHandler()
            while not next_file_flag:
                if period.use_time():
                    match (period.start_time < handler.endDatetime, period.end_time > handler.startDatetime):
                        case (True, True):
                            time_range = (period.start_time, period.end_time)
                            generate_flag = True
                            next_period_flag = period.end_time <= handler.endDatetime
                            next_file_flag = not next_period_flag
                        case (False, True):
                            next_file_flag = True
                        case (True, False):
                            next_period_flag = True
                else:
                    match (period.start_num < scan_num_sum + handler.totalScanNum, period.stop_num > scan_num_sum):
                        case (True, True):
                            time_range = handler.scanNumRange2DatetimeRange(
                                (max(period.start_num - scan_num_sum, 0),
                                 min(period.stop_num - scan_num_sum, handler.totalScanNum - 1)))
                            generate_flag = True
                            next_period_flag = period.stop_num <= scan_num_sum + handler.totalScanNum
                            next_file_flag = period.stop_num >= scan_num_sum + handler.totalScanNum
                        case (False, True):
                            next_file_flag = True
                        case (True, False):
                            next_period_flag = True

                if generate_flag:
                    info = cls(
                        start_time=time_range[0], end_time=time_range[1],
                        path=path.path, polarity=polarity, average_index=average_index)
                    results.append(info)

                if next_period_flag:
                    average_index = 0
                    i += 1
                    if i >= len(periods):
                        return results
                    period = periods[i]
                elif next_file_flag: # same period with next file
                    average_index += 1
                next_period_flag = False
                generate_flag = False
            next_file_flag = False

            scan_num_sum += handler.totalScanNum
        return results

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
        if origin == PATH_TYPE.THERMO.value:
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
