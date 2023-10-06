from datetime import datetime

from Orbitool.base import (AttrNdArray, BaseDatasetStructure, BaseRowStructure,
                           BaseStructure)
from Orbitool.base.extra_type_handlers import NdArray


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
