from typing import List, Optional
from datetime import datetime
from ..structures.file import FileSpectrumInfo
from ..structures.base import Field, BaseStructure


class SpectraListInfo(BaseStructure):
    h5_type = "spectra list info"

    selected_start_time: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
