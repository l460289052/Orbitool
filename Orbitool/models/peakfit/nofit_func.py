from typing import List
import numpy as np

from ...models.spectrum.spectrum import FittedPeak, Peak
from ..spectrum import getPeaksPositions
from .base_fit_func import BaseFunc


class NoFitFunc(BaseFunc):
    def func(self, mz: np.ndarray, params):
        return mz  # BUG

    def splitPeak(self, peak: Peak, split_num=None, force=False) -> List[FittedPeak]:
        id_split = np.where(getPeaksPositions(-peak.intensity))[0] + 1

        mz = peak.mz
        intensity = peak.intensity
        peaks = []
        if len(id_split) == 0:
            peaks.append(self.generate_peak(mz, intensity))
        else:
            peak_mz = mz[0: id_split[0] + 2]
            peak_intensity = intensity[0: id_split[0] + 2].copy()
            peak_intensity[-1] = 0
            peak_intensity[-2] /= 2
            peaks.append(self.generate_peak(peak_mz, peak_intensity))

            for l, r in zip(id_split, id_split[1:]):
                peak_mz = mz[l - 1:r + 2]
                peak_intensity = intensity[l - 1:r + 2].copy()
                peak_intensity[0] = 0
                peak_intensity[-1] = 0
                peak_intensity[1] /= 2
                peak_intensity[-2] /= 2

                peaks.append(self.generate_peak(peak_mz, peak_intensity))

            peak_mz = mz[id_split[-1] - 1:]
            peak_intensity = intensity[id_split[-1] - 1:].copy()
            peak_intensity[0] = 0
            peak_intensity[1] /= 2
            peaks.append(self.generate_peak(peak_mz, peak_intensity))

        return peaks

    def generate_peak(self, mz: np.ndarray, intensity: np.ndarray):
        pos = np.where(getPeaksPositions(intensity))[0][0] + 1
        return FittedPeak(
            mz, intensity,
            np.zeros((0,), dtype=float),
            mz[pos],
            intensity[pos],
            np.trapz(intensity, mz)
        )
