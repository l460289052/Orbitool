from functools import partial
from typing import List

import numpy as np

from Orbitool.base import BaseDatasetStructure, AttrList, NdArray

from .base import BaseInfo

zero = np.zeros(0)


class Gry(BaseDatasetStructure):
    x: NdArray[float, -1] = zero
    y: NdArray[float, -1] = zero
    size: NdArray[float, -1] = zero


class Clr(Gry):
    color: NdArray[float, -1] = zero
    labels: AttrList[str] = []


class MassDefectInfo(BaseInfo):
    is_dbe: bool = True
    clr_title: str = ""

    clr: Clr = Clr()
    gry: Gry = Gry()
