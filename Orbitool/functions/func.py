from typing import List
from copy import copy

import numpy as np

from ._func import getPeaks as _getPeaks, getNoise as _getNoise, denoiseWithLOD as _denoiseWithLOD
from .abstract import nullSendStatus
import OrbitoolBase

def getPeaks(spectrum: OrbitoolBase.Spectrum, indexRange: (int, int) = None, mzRange: (float, float) = None) -> List[OrbitoolBase.Peak]:
    '''
    get peak divided by 0, result peak may have many peakPoint
    '''
    peaksRange = _getPeaks(
        spectrum.mz, spectrum.intensity, indexRange, mzRange)
    return [OrbitoolBase.Peak(spectrum, range(rstart, rstop)) for rstart, rstop in peaksRange]

def getNoise(spectrum: OrbitoolBase.Spectrum,  quantile=0.7, sendStatus=nullSendStatus) -> (np.ndarray, np.ndarray):
    """
    @quantile: sort peaks by intensity, select num*quantile-th biggest peak
    """
    fileTime = spectrum.fileTime
    msg = "calc noise"
    sendStatus(fileTime, msg, -1, 0)
    peakAt, noise, LOD = _getNoise(
        spectrum.mz, spectrum.intensity,  quantile)
    return peakAt, noise, LOD

def denoiseWithLOD(spectrum: OrbitoolBase.Spectrum, LOD: (float, float), peakAt: np.ndarray = None, minus=False, sendStatus=OrbitoolBase.nullSendStatus) -> OrbitoolBase.Spectrum:
    fileTime = spectrum.fileTime
    msg = "denoising"
    sendStatus(fileTime, msg, -1, 0)

    newSpectrum = copy(spectrum)
    if peakAt is None:
        peakAt = peakAt_np(intensity)
    mz, intensity = _denoiseWithLOD(
        spectrum.mz, spectrum.intensity, LOD, peakAt, minus)
    newSpectrum.mz = mz
    newSpectrum.intensity = intensity
    newSpectrum.peaks = getPeaks(newSpectrum)
    return newSpectrum


def denoise(spectrum: OrbitoolBase.Spectrum,  quantile=0.7, minus=False, sendStatus=OrbitoolBase.nullSendStatus):
    peakAt, noise, LOD = getNoise(spectrum,  quantile, sendStatus)
    return noise, LOD, denoiseWithLOD(spectrum, LOD, peakAt, minus, sendStatus)

__all__ = ['getPeaks','getNoise','denoiseWithLOD','denoise']
