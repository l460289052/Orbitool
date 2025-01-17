from array import array
from typing import List
from datetime import datetime

from Orbitool.base import BaseDatasetStructure, Array
from ..formula import Formula, FormulaList


class TimeSeries(BaseDatasetStructure):
    position_min: float
    position_max: float

    range_sum: bool = False
    formulas: FormulaList = []

    times: List[datetime] = []
    positions: Array["d"] = array('d')
    intensity: Array["d"] = array('d')

    def append(self, time: datetime, intensity: float, position: float):
        self.times.append(time)
        self.positions.append(position)
        self.intensity.append(intensity)

    @classmethod
    def FactoryPositionRtol(cls, position: float, rtol: float, formulas: List[Formula] = []):
        delta = position * rtol
        return cls(position_min=position - delta, position_max=position + delta, range_sum=False, formulas=formulas.copy())

    def get_deviations(self):
        mid = (self.position_min + self.position_max) / 2
        return array("d", ((pos / mid - 1) * 1e6 for pos in self.positions))
