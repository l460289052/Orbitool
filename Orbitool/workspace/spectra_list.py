from typing import List, Optional
from datetime import datetime
from ..structures.file import SpectrumInfo
from ..structures.base import Field, BaseStructure


class SpectraListInfo(BaseStructure):
    h5_type = "spectra list info"

    file_spectrum_info_list: List[SpectrumInfo] = Field(default_factory=list)

    selected_start_time: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
