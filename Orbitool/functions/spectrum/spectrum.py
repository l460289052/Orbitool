from __future__ import annotations
from typing import List, Tuple

import numpy as np

from ...structures import spectrum
from ._spectrum import getNotZeroPositions, getPeaksPositions
from ._spectrum import splitPeaks as _splitPeaks


def removeZeroPositions(mz: np.ndarray, intensity: np.ndarray, min_intensity: float = 1e-6
                        ) -> Tuple[np.ndarray, np.ndarray]:
    position = getNotZeroPositions(intensity, min_intensity)
    return mz[position], intensity[position]


def splitPeaks(mz: np.ndarray, intensity: np.ndarray) -> List[spectrum.Peak]:
    ranges = _splitPeaks(mz, intensity)
    return [spectrum.Peak(mz=mz[r[0]:r[1]], intensity=intensity[r[0]:r[1]]) for r in ranges if r[0] < r[1]]
