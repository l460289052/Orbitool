import numpy as np
from datetime import timedelta, datetime
from typing import overload, List, Tuple, Iterable
from itertools import compress, chain

from ...utils import iterator


def part_by_time_interval(ids: list, start_times: List[datetime], end_times: List[datetime],
                          start_point: datetime, end_point: datetime, interval: timedelta
                          ) -> Iterable[Tuple[str, datetime, datetime, int]]:
    assert len(ids) == len(start_times) == len(end_times)
    times = np.arange(start_point, end_point + interval, interval)
    times[-1] = end_point
    select = np.empty((times.size - 1, len(ids)), bool)

    zip_input = list(zip(ids, start_times, end_times))
    for index, (_, start, end) in enumerate(zip_input):
        select[:, index] = (start < times[1:]) & (end > times[:-1])
    return chain.from_iterable((((value[0], time_s.astype(datetime), time_e.astype(datetime), i) for i, value in enumerate(values)) for slt, time_s, time_e in zip(select, times[:-1], times[1:]) if len(values := list(compress(zip_input, slt))) > 0))


def part_by_time_interval_fast(ids: list, start_times: List[datetime], end_times: List[datetime],
                               start_point: datetime, end_point: datetime, interval: timedelta
                               ) -> Iterable[Tuple[str, datetime, datetime, int]]:
    raise NotImplementedError()
    assert len(ids) == len(start_times) == len(end_times)
    it = iterator(zip(ids, start_times, end_times))

    while not it.end and it.value[1] < start_point:
        it.inc()
    if it.end:
        return []

    def get_end(start):
        end = start + interval
        return end_point if end > end_point else end

    parted = []
    start = start_point
    end = get_end(start)

    id_, id_start, id_end = it.value
    # method 1 (not tested)

    # while True:
    #     if end <= id_end:
    #         if end < id_start:
    #             start += (id_start / start) // interval * interval
    #             end = get_end(start)
    #             continue
    #         else:
    #             parted.append((id_, start, end, 0))
    #             start += interval
    #             end = get_end(start)
    #             if end == id_end:
    #                 if (ret:=it.inc())is not None:
    #                     id_, id_start, id_end = ret
    #                 else:
    #                     return parted
    #     else:
    #         index = 0
    #         while True:
    #             parted.append((id_, start, end, index))
    #             if (ret:=it.inc()) is not None:
    #                 id_, id_start, id_end = ret
    #                 if id_start > end:
    #                    break
    #             else:
    #                 return parted

    # method 2 (not tested)
    # index = 0
    # while True:
    #     if end <= id_end:
    #         if end < id_start:
    #             start += (id_start - start) // interval * interval
    #             end = get_end(start)
    #             index = 0
    #             continue
    #         parted.append((id_, start, end, index))
    #         start += interval
    #         end = get_end(start)
    #         index = 0
    #     else:  # end > id_end
    #         parted.append((id_, start, end, index))
    #         if (ret)
