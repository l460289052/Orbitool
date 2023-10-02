from typing import List
from ...models.spectrum.spectrum import Peak, FittedPeak
from .base_fit_func import BaseFunc
import numpy as np


def calculateResidual(raw_peaks: List[Peak], original_indexes: List[int], fitted_indexed_peaks: List[FittedPeak], fit_func: BaseFunc):
    mz = []
    intensity = []

    oindex = None
    omz = None
    ointensity = None

    for peak_oindex, peak in zip(original_indexes, fitted_indexed_peaks):
        if oindex != peak_oindex:
            oindex = peak_oindex
            opeak = raw_peaks[oindex]
            omz = opeak.mz
            ointensity = opeak.intensity.copy()
            mz.append(omz)
            intensity.append(ointensity)

        ointensity -= fit_func.func(omz, peak.fitted_param)

    mz = np.concatenate(mz)
    intensity = np.concatenate(intensity)

    return mz, intensity
