from functools import partial
from typing import List

import numpy as np

from Orbitool.base import BaseDatasetStructure, AttrList

from .base import BaseInfo

zero = partial(np.zeros, 0)


class Gry(BaseDatasetStructure):
    x: np.ndarray = zero
    y: np.ndarray = zero
    size: np.ndarray = zero


class Clr(Gry):
    color: np.ndarray = zero
    labels: AttrList[str] = None


class MassDefectInfo(BaseInfo):
    h5_type = "mass defect tab"

    is_dbe: bool = True
    clr_title: str = ""

    clr: Clr = Clr()
    gry: Gry = Gry()
