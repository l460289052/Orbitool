from typing import List, Optional
from datetime import datetime
from ..file import SpectrumInfo
from ..base import Field, BaseStructure


class SpectraListInfo(BaseStructure):
    h5_type = "spectra list info"

    file_spectrum_info_list: List[SpectrumInfo] = Field(default_factory=list)

    selected_start_time: Optional[datetime] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
