from datetime import datetime, timedelta
from typing import List
from ..file import FileSpectrumInfo, Path


start_dt = datetime(2000, 1, 1)
interval = timedelta(1)


class TmpInfo(FileSpectrumInfo):
    item_name = "tmp info"

    @classmethod
    def spectrum_iter(cls, paths: List[Path], polarity, timeRange):
        dt = start_dt
        for p in paths:  # each file has 10 spectra
            for i in range(10):
                yield p, dt
                dt += interval


def test_num_average_half():
    infos = TmpInfo.infosFromNumInterval(
        map(str, range(10)), 5, 1, None)

    for info in infos:
        assert round((info.end_time - info.start_time) / interval) == 4
        assert info.average_index == 0


def test_num_average_double():
    infos = TmpInfo.infosFromNumInterval(
        map(str, range(10)), 20, 1, None)

    for index, info in enumerate(infos):
        assert round((info.end_time - info.start_time) / interval) == 9
        assert info.average_index == index % 2


def test_num_average_some():
    infos = TmpInfo.infosFromNumInterval(
        map(str, range(10)), 3, 1, None)

    cnt = 3
    ind_cnt = 0
    for info in infos:
        if info.average_index:
            cnt += round((info.end_time - info.start_time) / interval) + 1
            ind_cnt += 1
        else:
            assert cnt == 3
            cnt = round((info.end_time - info.start_time) / interval) + 1
            ind_cnt = 0
