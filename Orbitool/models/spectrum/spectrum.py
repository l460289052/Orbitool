from datetime import datetime
from enum import Enum
from functools import cached_property

import numpy as np

from Orbitool.base import (AttrNdArray, BaseDatasetStructure, BaseRowStructure,
                           BaseStructure)
from Orbitool.base.extra_type_handlers import NdArray

from ...utils.formula import Formula, FormulaList


class PeakTags(str, Enum):
    Noise = 'N'
    Done = 'D'
    Fail = 'F'


class Peak(BaseDatasetStructure):
    mz: NdArray[float, -1]
    intensity: NdArray[float, -1]

    @cached_property
    def maxIntensity(self):
        return self.intensity.max()

    @cached_property
    def isPeak(self):
        return functions.getPeaksPositions(self.intensity)

    @cached_property
    def idPeak(self):
        return np.where(self.isPeak)[0]


class FittedPeak(Peak):
    fitted_param: AttrNdArray[float, -1]
    peak_position: float
    peak_intensity: float
    area: float

    tags: str = ""
    formulas: FormulaList = []


class Spectrum(BaseDatasetStructure):
    mz: NdArray['float64', -1]
    intensity: NdArray['float64', -1]
    path: str
    start_time: datetime
    end_time: datetime


class SpectrumInfo(BaseRowStructure):
    start_time: datetime
    end_time: datetime

    def get_show_str(self):
        return f"{self.start_time}-{self.end_time}"



from . import functions # avoid circular import
