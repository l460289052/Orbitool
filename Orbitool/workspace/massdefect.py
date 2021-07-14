from typing import List

import numpy as np

from ..structures.base import BaseStructure


class MassDefectInfo(BaseStructure):
    h5_type = "mass defect tab"

    is_dbe: bool = True
    element: str = ""

    clr_x: np.ndarray = np.zeros(0)
    clr_y: np.ndarray = np.zeros(0)
    clr_size: np.ndarray = np.zeros(0)
    clr_color: np.ndarray = np.zeros(0)

    gry_x: np.ndarray = np.zeros(0)
    gry_y: np.ndarray = np.zeros(0)
    gry_size: np.ndarray = np.zeros(0)
