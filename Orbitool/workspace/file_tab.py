from typing import List

import numpy as np

from ..structures import BaseStructure, field, Row
from ..structures.file import FileSpectrumInfo, PathList
from ..structures.HDF5 import StructureList
from ..structures.spectrum import Spectrum
from .base import Widget as BaseWidget


class FileTabInfo(BaseStructure):
    h5_type = "file tab"

    rtol: float = 1e-6
    spectrum_infos: Row[FileSpectrumInfo] = field(list)
    pathlist: PathList = field(PathList)


class Widget(BaseWidget[FileTabInfo]):
    raw_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, FileTabInfo)
