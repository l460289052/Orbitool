from typing import List, Tuple

import numpy as np

from ...structures.spectrum import Peak
from ._spectrum import getNotZeroPositions, getPeaksPositions
from ._spectrum import splitPeaks as _splitPeaks


def removeZeroPositions(mass: np.ndarray, intensity: np.ndarray, min_intensity: float = 1e-6
                        ) -> Tuple[np.ndarray, np.ndarray]:
    position = getNotZeroPositions(intensity, min_intensity)
    return mass[position], intensity[position]


def splitPeaks(mz: np.ndarray, intensity: np.ndarray) -> List[Peak]:
    ranges = _splitPeaks(mz, intensity)
    return [Peak(mz=mz[r[0]:r[1]], intensity=intensity[r[0]:r[1]]) for r in ranges]
