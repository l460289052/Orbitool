from typing import List
from datetime import datetime

from ..structures import BaseStructure, field, Row, BaseRowItem
from ..structures.timeseries import TimeSeries
from ..utils.formula import FormulaList
from .base import BaseInfo


class TimeSeriesInfoRow(BaseRowItem):
    h5_type = "time series info row"

    position_min: float
    position_max: float
    range_sum: bool = False
    time_min: datetime = None
    time_max: datetime = None
    formulas: FormulaList = field(list)

    @classmethod
    def FromTimeSeries(cls, timeseries: TimeSeries):
        return cls(
            position_min=timeseries.position_min,
            position_max=timeseries.position_max,
            range_sum=timeseries.range_sum,
            time_min=timeseries.times[0] if timeseries.times else None,
            time_max=timeseries.times[-1] if timeseries.times else None,
            formulas=timeseries.formulas
        )

    def get_name(self):
        if self.formulas:
            return ','.join(str(f) for f in self.formulas)
        else:
            if self.range_sum:
                return f"{self.position_min:.2f}-{self.position_max:.2f}"
            else:
                return format((self.position_min + self.position_max) / 2, '.5f')


class TimeseriesInfo(BaseInfo):
    h5_type = "timeseries tab"

    timeseries_infos: Row[TimeSeriesInfoRow] = field(list)
    show_index: int = -1
