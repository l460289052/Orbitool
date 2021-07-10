from typing import List
from ..structures.base import BaseStructure, Field
from ..structures.timeseries import TimeSeries


class TimeseriesInfo(BaseStructure):
    h5_type = "timeseries tab"

    series: List[TimeSeries] = Field(default_factory=list)

    show_index: int = -1
