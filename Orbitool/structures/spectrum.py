from __future__ import annotations

from datetime import datetime
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Iterable, List

import numpy as np
from h5py import string_dtype

from ..functions import spectrum
from ..utils.formula import Formula
from .base import BaseStructure, BaseRowItem, Field
from .HDF5 import AsciiLimit, Ndarray
from .HDF5.h5datatable import BaseDatatableType


class Peak(BaseRowItem):
    item_name = "Peak"
    mz: Ndarray[float, -1]
    intensity: Ndarray[float, -1]

    @cached_property
    def maxIntensity(self):
        return self.intensity.max()

    @cached_property
    def isPeak(self):
        return spectrum.getPeaksPositions(self.intensity)

    @cached_property
    def idPeak(self):
        return np.where(self.isPeak)[0]


if TYPE_CHECKING:
    class FormulaList(List[Formula], BaseDatatableType):
        dtype = string_dtype('utf-8')
else:
    class FormulaList(list, BaseDatatableType):
        dtype = string_dtype('utf-8')

        def __init__(self, value: Iterable = None):
            if value is None:
                super().__init__()
            else:
                value = [s if isinstance(s, Formula) else Formula(s)
                         for s in value]
                super().__init__(value)

        @classmethod
        def validate(cls, v):
            return v

        @staticmethod
        def convert_to_h5(value: FormulaList):
            return ','.join(str(f) for f in value)

        @staticmethod
        def convert_from_h5(value: str):
            if isinstance(value, bytes):
                value = value.decode()
            return [Formula(s) for s in value.split(',') if s.strip()]


class PeakTags(str, Enum):
    Noise = 'N'
    Done = 'D'
    Fail = 'F'


class FittedPeak(Peak):
    item_name = "FittedPeak"
    fitted_param: Ndarray[float, -1]
    peak_position: float
    peak_intensity: float
    area: float

    tags: str = ""
    formulas: FormulaList = Field(default_factory=list)


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
    formulas: FormulaList = Field(default_factory=FormulaList)
