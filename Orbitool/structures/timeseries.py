from array import array
from typing import List
from datetime import datetime
from .base import field
from .base_structure import BaseStructure
from .HDF5 import Array
from ..utils.formula import Formula, FormulaList


class TimeSeries(BaseStructure):
    h5_type = "time series"

    position_min: float
    position_max: float

    range_sum: bool = False
    formulas: FormulaList = field(list)

    times: List[datetime] = field(list)
    positions: Array[float] = field(lambda: array('d'))
    intensity: Array[float] = field(lambda: array('d'))

    def append(self, time, intensity, position=None):
        if not self.range_sum:
            assert position
            self.positions.append(position)
        self.times.append(time)
        self.intensity.append(intensity)

    @classmethod
    def FactoryPositionRtol(cls, position: float, rtol: float, formulas: List[Formula] = []):
        delta = position * rtol
        return cls(position - delta, position + delta, False, formulas.copy())

    def get_deviations(self):
        mid = (self.position_min + self.position_max) / 2
        return array("d", ((pos / mid - 1) * 1e6 for pos in self.positions))
