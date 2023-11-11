from typing import List
from datetime import datetime, timedelta

from Orbitool.base import BaseRowStructure
from ..formula import FormulaList
from ..timeseries import TimeSeries
from .base import BaseInfo

validated_datetime = datetime(1900, 1, 1)
invalid_datetime = validated_datetime - timedelta(1000)

class TimeSeriesInfoRow(BaseRowStructure):
    position_min: float
    position_max: float
    range_sum: bool = False
    time_min: datetime = None
    time_max: datetime = None
    formulas: FormulaList = []

    @classmethod
    def FromTimeSeries(cls, timeseries: TimeSeries):
        return cls(
            position_min=timeseries.position_min,
            position_max=timeseries.position_max,
            range_sum=timeseries.range_sum,
            time_min=timeseries.times[0] if timeseries.times else invalid_datetime,
            time_max=timeseries.times[-1] if timeseries.times else invalid_datetime,
            formulas=timeseries.formulas
        )
    
    def valid(self):
        return self.time_min > validated_datetime

    def get_name(self):
        if self.formulas:
            return ','.join(str(f) for f in self.formulas)
        else:
            if self.range_sum:
                return f"{self.position_min:.2f}-{self.position_max:.2f}"
            else:
                return format((self.position_min + self.position_max) / 2, '.5f')


class TimeseriesInfo(BaseInfo):
    timeseries_infos: List[TimeSeriesInfoRow] = []
    show_index: int = -1
