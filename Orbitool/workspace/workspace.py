from typing import Generic, List, Optional, Type, TypeVar, Union
import shutil

from pydantic import BaseModel, Field

from ..structures.base import BaseStructure, BaseTableItem
from ..structures.HDF5 import H5File, H5Obj, Ndarray

from .base import Widget
from .file_tab import Widget as FileWidget
from .spectra_list import SpectraListInfo
from .noise_tab import NoiseTabInfo
from .peak_shape import PeakShapeInfo
from .calibration import Widget as CalibrationWidget
from .peak_fit import PeakFitInfo

from .formula import FormulaInfo

T = TypeVar("T")


class WorkspaceInfo(BaseStructure):
    h5_type = "workspace info"

    version: str = "2.0.0"
    hasRead: bool = False


class WorkSpace(H5File):
    def __init__(self, path: str = None) -> None:
        super().__init__(path)
        self.info: WorkspaceInfo = self.read("info") if "info" in self else WorkspaceInfo(
        )
        self.widgets = []

        self.file_tab = self.visit_or_create_widget_specific(
            "file tab", FileWidget)
        self.spectra_list = self.visit_or_create_widget(
            "spectra list", SpectraListInfo)
        self.noise_tab = self.visit_or_create_widget("noise tab", NoiseTabInfo)
        self.peak_shape_tab = self.visit_or_create_widget(
            "peak shape tab", PeakShapeInfo)
        self.calibration_tab = self.visit_or_create_widget_specific(
            "calibration tab", CalibrationWidget)
        self.peakfit_tab = self.visit_or_create_widget(
            "peak fit tab", PeakFitInfo)

        self.formula_docker = self.visit_or_create_widget(
            "formula docker", FormulaInfo)

    def save(self):
        self.write("info", self.info)
        for widget in self.widgets:
            widget.save()

    def in_memory(self):
        return not self._file

    def close_as(self, path: str):
        self.save()
        self.close()

        if self._file:
            shutil.copy(self._io, path)
        else:
            with open(path, 'wb') as f:
                f.write(self._io.getbuffer())

    def visit_or_create_widget(self, path: str, info_type: Type[T]) -> Widget[T]:
        if path in self:
            widget = Widget(self._obj[path], info_type)
        else:
            widget = Widget(self._obj.create_group(path), info_type)
        self.widgets.append(widget)
        return widget

    def visit_or_create_widget_specific(self, path: str, widget_type: Type[T]) -> T:
        if path in self:
            widget = widget_type(self._obj[path])
        else:
            widget = widget_type(self._obj.create_group(path))
        self.widgets.append(widget)
        return widget
