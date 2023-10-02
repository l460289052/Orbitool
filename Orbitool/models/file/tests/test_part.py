from datetime import datetime, timedelta
from ..part_file import generage_periods

delta = timedelta(seconds=1)


def to_dt(npdt):
    return [a.astype(datetime) for a in npdt]


def eval(rets, id_times, start_time, end_time, interval):
    cnt = 0
    for id, start, end, index in rets:
        if index == 0:
            cnt += 1
        tmp = (start - start_time) / interval
        t_s, t_e = id_times[id]
        assert t_s < end and start < t_e  # cross
        if index == 0:
            assert abs(tmp - round(tmp)) * interval < delta or\
                abs(start - t_s) < delta
        assert end < start + interval or \
            abs(end - start - interval) < delta or \
            abs(end - end_time) < delta
    return cnt

