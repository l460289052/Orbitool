from datetime import datetime
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Iterable, List

import numpy as np
from h5py import Group

from ..functions import spectrum
from ..utils.formula import Formula, FormulaList
from .base import field
from .base_row import BaseRowItem, RowDTypeHandler
from .base_structure import BaseStructure
from .HDF5 import AsciiLimit, NdArray
from .HDF5.h5type_handlers.simple_handler import StrHandler


class Peak(BaseRowItem):
    item_name = "Peak"
    mz: NdArray[float, -1]
    intensity: NdArray[float, -1]

    @cached_property
    def maxIntensity(self):
        return self.intensity.max()

    @cached_property
    def isPeak(self):
        return spectrum.getPeaksPositions(self.intensity)

    @cached_property
    def idPeak(self):
        return np.where(self.isPeak)[0]


class PeakTags(str, Enum):
    Noise = 'N'
    Done = 'D'
    Fail = 'F'


class FittedPeak(Peak):
    item_name = "FittedPeak"
    fitted_param: NdArray[float, -1]
    peak_position: float
    peak_intensity: float
    area: float

    tags: str
    formulas: FormulaList = field(list)


class Spectrum(BaseStructure):
    h5_type = "Spectrum"

    path: str
    mz: np.ndarray
    intensity: np.ndarray
    start_time: datetime
    end_time: datetime


class SpectrumInfo(BaseRowItem):
    item_name = "spectrum info"

    start_time: datetime
    end_time: datetime


class MassListItem(BaseRowItem):
    item_name = "MassList"
    position: float
    formulas: FormulaList = field(list)
