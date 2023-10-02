from itertools import chain
from typing import List, Literal, Optional

import numpy as np

from Orbitool.base import BaseStructure

from ..spectrum.spectrum import FittedPeak, Peak, Spectrum
from Orbitool.functions.binary_search import indexBetween_np, indexNearest, indexFirstBiggerThan


def get_peak_mz_min(peaks: List[Peak], index: int):
    return peaks[index].mz.min()


def get_peak_mz_max(peaks: List[Peak], index: int):
    return peaks[index].mz.max()


def get_peak_position(peaks: List[FittedPeak], index: int):
    return peaks[index].peak_position


def get_peak_intensity(peak: FittedPeak):
    return peak.peak_intensity


class BaseFunc(BaseStructure):
    def func(self, mz: np.ndarray, params):
        pass

    def splitPeak(self, peak: Peak, split_num=None, force=False) -> List[FittedPeak]:
        pass

    def get_peak_max(self, peaks: List[Peak], min_mz: float, max_mz: float, target: Literal["peak_intensity", "area"] = "peak_intensity"):
        lindex = indexFirstBiggerThan(peaks, min_mz, method=get_peak_mz_max)
        rindex = indexFirstBiggerThan(peaks, max_mz, method=get_peak_mz_min)

        peaks = peaks[lindex:rindex]
        peaks: List[FittedPeak] = list(
            chain.from_iterable(map(self.splitPeak, peaks)))

        peaks = [peak for peak in peaks
                 if min_mz < peak.peak_position < max_mz]

        if len(peaks) > 0:
            peak = max(peaks, key=lambda p: getattr(p, target))
            return peak.peak_position, getattr(peak, target)

        return None

    def get_peak_sum(self, peaks: List[Peak], target: Literal["peak_intensity", "area"] = "peak_intensity") -> float:
        return sum(sum(getattr(p, target) for p in self.splitPeak(peak)) for peak in peaks)
