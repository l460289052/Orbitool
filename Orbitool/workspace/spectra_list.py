from datetime import datetime
from typing import List, Optional

import numpy as np

from ..structures.base import BaseStructure, Field
from ..structures.file import FileSpectrumInfo


class SpectraListInfo(BaseStructure):
    h5_type = "spectra list info"

    shown_indexes: List[int] = Field(default_factory=list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
