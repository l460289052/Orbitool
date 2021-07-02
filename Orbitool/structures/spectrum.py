from typing import List
from .base import BaseStructure, Field, BaseTableItem
from .HDF5 import Ndarray
from ..utils.formula import Formula
from ..functions import spectrum
from datetime import datetime
import numpy as np
from functools import cached_property


class Peak(BaseTableItem):
    item_name = "Peak"
    mz: Ndarray[float, -1]
    intensity: Ndarray[float, -1]
    split_num: int = -1
    original_index: int = -1

    @cached_property
    def maxIntensity(self):
        return self.intensity.max()

    @cached_property
    def isPeak(self):
        return spectrum.getPeaksPositions(self.intensity)

    @cached_property
    def idPeak(self):
        return np.where(self.isPeak)[0]


class FittedPeak(Peak):
    item_name = "FittedPeak"
    fitted_param: Ndarray[float, -1]
    peak_position: float
    peak_intensity: float
    area: float

    formulas: str = ""

    def get_formula_list(self) -> List[Formula]:
        return list(map(Formula, self.formulas.split(', ')))

    def set_formula_list(self, formulas: List[Formula]):
        self.formulas = ', '.join(map(str, formulas))


class Spectrum(BaseStructure):
    h5_type = "Spectrum"

    path: str
    mz: np.ndarray
    intensity: np.ndarray
    start_time: datetime
    end_time: datetime


class SpectrumList(BaseStructure):
    h5_type = "SpectrumList"


# class MassListItem
