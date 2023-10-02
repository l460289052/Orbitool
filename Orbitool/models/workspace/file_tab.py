from typing import List

from .base import BaseInfo
from ..file import FileSpectrumInfo, PathList, PeriodItem


class FileTabInfo(BaseInfo):
    rtol: float = 1e-6
    spectrum_infos: List[FileSpectrumInfo] = []
    pathlist: PathList = PathList()
    periods: List[PeriodItem] = None
