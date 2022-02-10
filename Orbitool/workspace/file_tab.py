from typing import List

import numpy as np

from ..structures import BaseStructure, field, Row
from ..structures.file import FileSpectrumInfo, PathList, PeriodItem


class FileTabInfo(BaseStructure):
    h5_type = "file tab"

    rtol: float = 1e-6
    spectrum_infos: Row[FileSpectrumInfo] = field(list)
    pathlist: PathList = field(PathList)
    periods: Row[PeriodItem] = None
