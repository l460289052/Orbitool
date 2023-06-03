from typing import List
from ..structures import BaseStructure, field, Row
from ..structures.timeseries import TimeSeries
from .base import BaseInfo


class TimeseriesInfo(BaseInfo):
    h5_type = "timeseries tab"

    series: List[TimeSeries] = field(list)

    show_index: int = -1
