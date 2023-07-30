import numpy as np
from datetime import timedelta, datetime
from typing import overload, List, Tuple, Iterable
from itertools import compress, chain


def generage_periods(start_point: datetime, end_point: datetime, interval: timedelta) -> Iterable[Tuple[datetime, datetime]]:
    times = np.arange(start_point, end_point + interval, interval)
    times[-1] = end_point
    times = times.astype(datetime)
    return zip(times, times[1:])


def part_by_periods(ids: List[str], start_times: List[datetime], end_times: List[datetime],
                    periods: Iterable[Tuple[datetime, datetime]]) -> Iterable[Tuple[str, datetime, datetime, int]]:
    assert len(ids) == len(start_times) == len(end_times)
    periods = np.array(list(periods))
    select = np.empty((len(periods), len(ids)), bool)

    zip_input = list(zip(ids, start_times, end_times))
    for index, (_, start, end) in enumerate(zip_input):
        select[:, index] = (start < periods[:, 1]) & (end > periods[:, 0])

    periods = periods.astype(datetime)
    for slt, (time_s, time_e) in zip(select, periods):
        for i, value in enumerate(compress(zip_input, slt)):
            yield value[0], max(time_s, value[1]), min(time_e, value[2]), i


def generate_num_periods(start_scan_num: int, stop_scan_num: int, interval: int):
    """
        @return: np.array, shape=(n, 2)
    """
    assert interval > 0
    start_points = np.arange(start_scan_num, stop_scan_num, interval)
    end_points = start_points + interval
    end_points[-1] = min(end_points[-1], stop_scan_num)
    return np.stack((start_points, end_points), 1)
