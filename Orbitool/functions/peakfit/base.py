from itertools import chain
from typing import List

import numpy as np

from ...structures.spectrum import FittedPeak, Peak, Spectrum
from ..binary_search import indexBetween_np, indexNearest, indexFirstBiggerThan
from ..spectrum import splitPeaks


def get_peak_mz_min(peaks: List[Peak], index):
    return peaks[index].mz.min()


def get_peak_mz_max(peaks: List[Peak], index):
    return peaks[index].mz.max()


def get_peak_position(peaks: List[FittedPeak], index):
    return peaks[index].peak_position


def get_peak_intensity(peak: FittedPeak):
    return peak.intensity


class BaseFunc:
    def func(self, mz: np.ndarray, params):
        pass

    def splitPeak(self, peak: Peak, split_num=None, force=False) -> List[FittedPeak]:
        pass

    def fetchNearestPeak(self, spectrum: Spectrum, point: float, intensity_filter: float, delta=5):
        l, r = indexBetween_np(spectrum.mz, (point - delta, point + delta))
        mz = spectrum.mz[l:r]
        intensity = spectrum.intensity[l:r]
        peaks = splitPeaks(mz, intensity)
        if intensity_filter > 0:
            peaks = [peak for peak in peaks if peak.maxIntensity >
                     intensity_filter]
        index = indexNearest(peaks, point, method=get_peak_mz_min)
        if index > 0:
            peaks = [peaks[index - 1], peaks[index]]
        else:
            peaks = [peaks[index]]

        peaks = list(chain.from_iterable(map(self.splitPeak, peaks)))
        index = indexNearest(peaks, point, method=get_peak_position)
        return peaks[index]

    def fetchTimeseries(self, peaks: List[Peak], min_mz: float, max_mz: float):
        lindex = indexFirstBiggerThan(peaks, min_mz, method=get_peak_mz_max)
        rindex = indexFirstBiggerThan(peaks, max_mz, method=get_peak_mz_min)

        peaks = peaks[lindex:rindex]
        peaks: List[FittedPeak] = list(
            chain.from_iterable(map(self.splitPeak, peaks)))

        peaks = [peak for peak in peaks
                 if min_mz < peak.peak_position < max_mz]

        if len(peaks) > 0:
            peak = max(peaks, key=get_peak_intensity)
            return peak.peak_intensity
        return None
