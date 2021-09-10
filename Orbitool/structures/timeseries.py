from array import array
from typing import List
from datetime import datetime
from .base import BaseStructure, Field


class TimeSeries(BaseStructure):
    h5_type = "time series"

    position_min: float
    position_max: float

    times: List[datetime] = Field(default_factory=list)
    intensity = array('i')

    tag: str

    def append(self, time, intensity):
        self.times.append(time)
        self.intensity.append(intensity)

    @classmethod
    def FactoryPositionRtol(cls, position: float, rtol: float, tag: str):
        delta = position * rtol
        return cls(position_min=position - delta, position_max=position + delta, tag=tag)
