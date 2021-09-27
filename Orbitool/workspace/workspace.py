
import shutil
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union

from ..structures import BaseStructure, BaseRowItem
from ..structures.HDF5 import H5File
from .base import Widget
from .calibration import Widget as CalibrationWidget
from .file_tab import Widget as FileWidget
from .formula import FormulaInfo
from .massdefect import MassDefectInfo
from .masslist import MassListInfo
from .noise_tab import NoiseTabInfo
from .peak_fit import PeakFitInfo
from .peak_shape import PeakShapeInfo
from .spectra_list import SpectraListInfo
from .timeseries import TimeseriesInfo

T = TypeVar("T")


LAST_SUPPORT_VERSION = "2.0.2"
VERSION = "2.1.1"

class WorkspaceInfo(BaseStructure):
    h5_type = "workspace info"

    version: str = VERSION


class WorkSpace(H5File):
    def __init__(self, path: str = None) -> None:
        super().__init__(path)
        self.info: WorkspaceInfo = self.read("info") if "info" in self else WorkspaceInfo(
        )
        self.widgets: Dict[str, Widget] = {}

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
        self.massdefect_tab = self.visit_or_create_widget(
            "mass detect tab", MassDefectInfo)
        self.timeseries_tab = self.visit_or_create_widget(
            "time series tab", TimeseriesInfo)

        self.formula_docker = self.visit_or_create_widget(
            "formula docker", FormulaInfo)
        self.masslist_docker = self.visit_or_create_widget(
            "masslist docker", MassListInfo)
        self.peaklist_docker = self.visit_or_create_widget(
            "peaklist docker", BaseStructure)

    def save(self):
        self.write("info", self.info)
        for widget in self.widgets.values():
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
        self.widgets[path] = widget
        return widget

    def visit_or_create_widget_specific(self, path: str, widget_type: Type[T]) -> T:
        if path in self:
            widget = widget_type(self._obj[path])
        else:
            widget = widget_type(self._obj.create_group(path))
        self.widgets[path] = widget
        return widget

    def load_config(self, another: 'WorkSpace'):
        for key, widget in self.widgets.items():
            widget.ui_state = another.widgets[key].ui_state

        self.noise_tab.info.general_setting = another.noise_tab.info.general_setting
        self.calibration_tab.info.ions = another.calibration_tab.info.ions
        self.formula_docker.info = another.formula_docker.info
        self.masslist_docker.info = another.masslist_docker.info
