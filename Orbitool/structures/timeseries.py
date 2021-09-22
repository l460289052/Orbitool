from array import array
from typing import List
from datetime import datetime
from .base import field
from .base_structure import BaseStructure
from .HDF5 import Array


class TimeSeries(BaseStructure):
    h5_type = "time series"

    position_min: float
    position_max: float

    tag: str

    times: List[datetime] = field(list)
    intensity: Array[float] = field(lambda: array('d'))

    def append(self, time, intensity):
        self.times.append(time)
        self.intensity.append(intensity)

    @classmethod
    def FactoryPositionRtol(cls, position: float, rtol: float, tag: str):
        delta = position * rtol
        return cls(position - delta, position + delta, tag)
