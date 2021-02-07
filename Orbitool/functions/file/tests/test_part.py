import numpy as np
from datetime import datetime, timedelta
from Orbitool.functions.file import part_by_time_interval

delta = np.timedelta64(timedelta(seconds=1))


def eval(rets, id_times, start_time, end_time, interval):
    interval = np.timedelta64(interval)
    cnt = 0
    for id, start, end, index in rets:
        if index == 0:
            cnt += 1
        tmp = (start - start_time) / interval
        assert abs(tmp - round(tmp)) * interval < delta
        assert abs(end - start - interval) < delta or abs(end -
                                                          end_time) < delta
        t_s, t_e = id_times[id]
        assert t_s < end and start < t_e  # cross
    return cnt


def continuous_time_check(start, end, file_interval, interval):
    starts = np.arange(start, end, file_interval)
    file_interval = np.timedelta64(file_interval)
    ends = starts + file_interval
    ids = range(len(starts))
    id_times = {id: (start, end) for id, start, end in zip(ids, starts, ends)}
    rets = part_by_time_interval(ids, starts, ends, start, end, interval)
    now_time = np.datetime64(start)

    cnt = eval(rets, id_times, now_time, ends[-1], interval)

    tgt = (end - start) / interval
    if (tgt - int(tgt)) * timedelta(1) > delta:
        tgt = int(tgt) + 1
    else:
        tgt = int(tgt)
    assert cnt == tgt


def test_datetime():
    continuous_time_check(datetime(2000, 1, 1), datetime(
        2000, 1, 10), timedelta(2), timedelta(1))


def test_small_interval():
    continuous_time_check(datetime(2000, 1, 1), datetime(
        2000, 1, 3), timedelta(1), timedelta(minutes=7))


def test_big_interval():
    continuous_time_check(datetime(2000, 1, 1), datetime(
        2000, 1, 30), timedelta(1), timedelta(5.5))


def test_file_interval():
    starts = np.array(
        [datetime(2000, 1, 1), datetime(2000, 1, 10)], dtype='M8[us]')
    ends = starts + np.timedelta64(timedelta(1))

    ids = range(len(starts))
    id_times = {id: (start, end) for id, start, end in zip(ids, starts, ends)}

    interval = timedelta(hours=10)
    rets = part_by_time_interval(ids, starts, ends, datetime(
        2000, 1, 1), datetime(2000, 1, 11), interval)
    
    cnt = eval(rets, id_times, starts[0], ends[-1],interval)

