from typing import Tuple
import numpy as np
from ._spectrum import getPeaksPositions, getNotZeroPositions

def removeZeroPositions(mass: np.ndarray, intensity: np.ndarray, min_intensity: float = 1e-6
                        ) -> Tuple[np.ndarray, np.ndarray]:
    position = getNotZeroPositions(intensity, min_intensity)
    return mass[position], intensity[position]
