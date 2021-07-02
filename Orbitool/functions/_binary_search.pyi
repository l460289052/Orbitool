from typing import Tuple
import numpy as np


def indexNearest(array: np.ndarray, value,
                 indexRange: tuple = None) -> int: ...


def indexBetween(array: np.ndarray, valueRange: tuple,
                 indexRange: tuple = None) -> Tuple[int, int]: ...
