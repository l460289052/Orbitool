from typing import Tuple
import numpy as np


def getPeaksPositions(intensity: np.ndarray) -> np.ndarray: ...


def getNotZeroPositions(intensity: np.ndarray,
                        min_intensity: float = 1e-6) -> np.ndarray: ...
