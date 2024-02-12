import numpy as np
from datetime import timedelta, datetime
from typing import overload, List, Tuple, Iterable


class IFileHandler:
    totalScanNum: int

    def datetimeRange2ScanNumRange(self, timeRange: Tuple[datetime, datetime]) -> Tuple[int, int]:
        pass


def generate_periods(start_point: datetime, end_point: datetime, interval: timedelta) -> Iterable[Tuple[datetime, datetime]]:
    times = np.arange(start_point, end_point + interval, interval)
    times[-1] = end_point
    times = times.astype(datetime)
    return zip(times, times[1:])


def get_num_range_from_ranges(handlers: Iterable[IFileHandler], timeRange: Tuple[datetime, datetime]):
    total_scan_num = 0
    start_scan_num = -1
    stop_scan_num = -1
    for handler in handlers:
        start, stop = handler.datetimeRange2ScanNumRange(timeRange)
        if start < stop:
            if start_scan_num < 0:
                start_scan_num = total_scan_num + start
            stop_scan_num = total_scan_num + stop
        total_scan_num += handler.totalScanNum
    return start_scan_num, stop_scan_num, total_scan_num


def generate_num_periods(start_scan_num: int, stop_scan_num: int, interval: int):
    """
        @return: np.array, shape=(n, 2)
    """
    assert interval > 0
    start_points = np.arange(start_scan_num, stop_scan_num, interval)
    end_points = start_points + interval
    end_points[-1] = min(end_points[-1], stop_scan_num)
    return np.stack((start_points, end_points), 1)
