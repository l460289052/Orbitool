from typing import List
from ...structures.spectrum import Peak, FittedPeak
from .base import BaseFunc
import numpy as np


def calculateResidual(raw_peaks: List[Peak], fitted_indexed_peaks: List[FittedPeak], fit_func: BaseFunc):
    mz = []
    intensity = []

    oindex = None
    omz = None
    ointensity = None

    for peak in fitted_indexed_peaks:
        if oindex != peak.original_index:
            oindex = peak.original_index
            opeak = raw_peaks[oindex]
            omz = opeak.mz
            ointensity = opeak.intensity.copy()
            mz.append(omz)
            intensity.append(ointensity)

        ointensity -= fit_func.func(omz, peak.fitted_param)

    mz = np.concatenate(mz)
    intensity = np.concatenate(intensity)

    return mz, intensity
