from functools import partial
from typing import List

import numpy as np

from ..structures import BaseStructure, field
from .base import BaseInfo

zero = partial(np.zeros, 0)

class MassDefectInfo(BaseInfo):
    h5_type = "mass defect tab"

    is_dbe: bool = True
    clr_title: str = ""

    clr_x: np.ndarray = field(zero)
    clr_y: np.ndarray = field(zero)
    clr_size: np.ndarray = field(zero)
    clr_color: np.ndarray = field(zero)
    clr_labels: List[str] = None

    gry_x: np.ndarray = field(zero)
    gry_y: np.ndarray = field(zero)
    gry_size: np.ndarray = field(zero)
