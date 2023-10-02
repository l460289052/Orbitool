from typing import List, Tuple
import numpy as np


def getPeaksPositions(intensity: np.ndarray) -> np.ndarray:
    """
    intensity = [0, 1, 2, 1, 0]
    return: [False, True, False]
    """
    pass


def getNotZeroPositions(intensity: np.ndarray,
                        min_intensity: float = 1e-6) -> np.ndarray: ...


def splitPeaks(mz: np.ndarray, intensity: np.ndarray) -> np.ndarray:
    """
    return List[Tuple[int, int]] means left and right of a peak
    """
    pass


def safeCutSpectrum(mz: np.ndarray, intensity: np.ndarray, mzMin: float, mzMax: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    return mz, intensity
    """
    pass


def safeSplitSpectrum(mz: np.ndarray, intensity: np.ndarray, points: np.ndarray) -> List[np.ndarray]:
    """
    return [mz split by points]
    """
    pass
