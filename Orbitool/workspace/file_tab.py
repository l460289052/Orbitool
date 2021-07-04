from ..structures.base import BaseStructure, Field
from ..structures.file import PathList, FileSpectrumInfo
from ..structures.spectrum import Spectrum
from ..structures.HDF5 import StructureList
from .base import Widget as BaseWidget
from typing import List


class FileTabInfo(BaseStructure):
    h5_type = "file tab"

    spectrum_infos: List[FileSpectrumInfo] = Field(default_factory=list)
    pathlist: PathList = Field(default_factory=PathList)


class Widget(BaseWidget[FileTabInfo]):
    raw_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, FileTabInfo)
