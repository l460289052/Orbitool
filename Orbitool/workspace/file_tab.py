from typing import List

import numpy as np

from ..structures.base import BaseStructure, Field
from ..structures.file import FileSpectrumInfo, PathList
from ..structures.HDF5 import StructureList
from ..structures.spectrum import Spectrum
from .base import Widget as BaseWidget


class FileTabInfo(BaseStructure):
    h5_type = "file tab"

    rtol:float = 1e-6
    spectrum_infos: List[FileSpectrumInfo] = Field(default_factory=list)
    pathlist: PathList = Field(default_factory=PathList)


class Widget(BaseWidget[FileTabInfo]):
    raw_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, FileTabInfo)
