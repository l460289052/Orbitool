from typing import Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, Field

from ..structures.base import BaseStructure, BaseTableItem
from ..structures.file import PathList, SpectrumInfo
from ..structures.HDF5 import H5File, H5Obj, Ndarray

from .base import Widget
from .spectra_list import SpectraListInfo
from .noise_tab import NoiseTabInfo
from .peak_shape import PeakShapeInfo
from .calibration import CalibratorInfo


T = TypeVar("T")


class WorkspaceInfo(BaseStructure):
    h5_type = "workspace info"

    pathlist: PathList = Field(default_factory=PathList)
    hasRead: bool = False


class WorkSpace(H5File):
    def __init__(self, path: str = None) -> None:
        super().__init__(path)
        self.info: WorkspaceInfo = self.read("info") if "info" in self else WorkspaceInfo(
        )

        self.spectra_list = self.visit_or_create_widget(
            "spectra list", SpectraListInfo)
        self.noise_tab = self.visit_or_create_widget("noise tab", NoiseTabInfo)
        self.peak_shape_tab = self.visit_or_create_widget(
            "peak shape tab", PeakShapeInfo)
        self.calibration_tab = self.visit_or_create_widget(
            "calibration tab", CalibratorInfo)

        self.widgets: List[Widget] = [self.spectra_list, self.noise_tab]

    def save(self):
        self.write("info", self.info)
        for widget in self.widgets:
            widget.save()

    def visit_or_create_widget(self, path: str, info_class: Type[T]) -> Widget[T]:
        if path in self:
            return Widget(self._obj[path], info_class)
        return Widget(self._obj.create_group(path), info_class)
