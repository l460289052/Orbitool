import numpy as np
from ._spectrum import getPeaksPositions as _getPeaksPositions, getNotZeroPositions as _getNotZeroPositions

def getPeaksPositions(intensity:np.ndarray) -> np.ndarray:
    is_peak = _getPeaksPositions(intensity)
    return is_peak

def getNotZeroPositions(intensity:np.ndarray, min_intensity:float=1e-6)->np.ndarray:
    select = _getNotZeroPositions(intensity, min_intensity)
    return select