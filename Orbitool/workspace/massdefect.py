from typing import List

import numpy as np

from ..structures import BaseStructure, field
from .base import BaseInfo


class MassDefectInfo(BaseInfo):
    h5_type = "mass defect tab"

    is_dbe: bool = True
    clr_title: str = ""

    clr_x: np.ndarray = np.zeros(0)
    clr_y: np.ndarray = np.zeros(0)
    clr_size: np.ndarray = np.zeros(0)
    clr_color: np.ndarray = np.zeros(0)
    clr_labels: List[str] = None

    gry_x: np.ndarray = np.zeros(0)
    gry_y: np.ndarray = np.zeros(0)
    gry_size: np.ndarray = np.zeros(0)
