from ..structures.base import BaseStructure, Field
from ..structures.file import PathList, SpectrumInfo


class FileTabInfo(BaseStructure):
    h5_type = "file tab"

    pathlist: PathList = Field(default_factory=PathList)
