from typing import List

import numpy as np

from .base import BaseInfo
from ..structures import BaseStructure, field, Row
from ..models.file.file import FileSpectrumInfo, PathList, PeriodItem


class FileTabInfo(BaseInfo):
    h5_type = "file tab"

    rtol: float = 1e-6
    spectrum_infos: Row[FileSpectrumInfo] = field(list)
    pathlist: PathList = field(PathList)
    periods: Row[PeriodItem] = None
