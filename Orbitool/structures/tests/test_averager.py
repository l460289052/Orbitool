from typing import List
from ..file import FileSpectrumInfo, Path


class TmpInfo(FileSpectrumInfo):
    item_name = "tmp info"
    start_time: int
    end_time: int

    @classmethod
    def spectrum_iter(cls, paths: List[Path], polarity, timeRange):
        cnt = 0
        for p in paths:
            for i in range(10):
                yield p, cnt
                cnt += 1


def test_num_average_half():
    infos = TmpInfo.generate_infos_from_paths_by_number(
        map(str, range(10)), 1e-6, 5, 1, None)

    for info in infos:
        assert info.end_time - info.start_time == 4
        assert info.average_index == 0


def test_num_average_double():
    infos = TmpInfo.generate_infos_from_paths_by_number(
        map(str, range(10)), 1e-6, 20, 1, None)

    for index, info in enumerate(infos):
        assert info.end_time - info.start_time == 9
        assert info.average_index == index % 2


def test_num_average_some():
    infos = TmpInfo.generate_infos_from_paths_by_number(
        map(str, range(10)), 1e-6, 3, 1, None)

    cnt = 3
    ind_cnt = 0
    for info in infos:
        if info.average_index:
            cnt += info.end_time - info.start_time + 1
            ind_cnt += 1
        else:
            assert cnt == 3
            cnt = info.end_time - info.start_time + 1
            ind_cnt = 0
