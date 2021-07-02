from typing import List

from ...structures.spectrum import FittedPeak, Peak, Spectrum
from ..binary_search import indexBetween_np, indexNearest
from ..spectrum import splitPeaks

from itertools import chain


class BaseFunc:
    def splitPeak(self, peak: Peak, split_num=None, force=False) -> List[FittedPeak]:
        pass

    def fetchNearestPeak(self, spectrum: Spectrum, point: float, intensity_filter:float, delta=5):
        l, r = indexBetween_np(spectrum.mz, (point - delta, point + delta))
        mz = spectrum.mz[l:r]
        intensity = spectrum.intensity[l:r]
        peaks = splitPeaks(mz, intensity)
        peaks = [peak for peak in peaks if peak.maxIntensity > intensity_filter]
        peaks = list(chain.from_iterable(map(self.splitPeak, peaks)))
        index = indexNearest(peaks, point, method=(
            lambda peaks, index: peaks[index].peak_position))
        return peaks[index]
