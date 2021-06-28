from datetime import datetime
from typing import Generic, List, Type, TypeVar, Union, Optional

import numpy as np
from pydantic import BaseModel, Field

from ..utils import readers
from ..utils.formula import Formula
from .base import BaseStructure, BaseTableItem
from .file import FileList, SpectrumInfo, setFileReader
from .HDF5 import H5File, H5Obj, Ndarray
from .spectrum import Spectrum
from .. import config

setFileReader(readers.ThermoFile)

T = TypeVar("T")


class Widget(H5Obj, Generic[T]):
    def __init__(self, obj, info_class: Type[T]) -> None:
        super().__init__(obj)
        self._info_class = info_class
        self.info: T = self["info"] if "info" in self else info_class()

    def save(self):
        self["info"] = self.info


class WorkspaceInfo(BaseStructure):
    h5_type = "workspace info"

    filelist: FileList = Field(default_factory=FileList)


class SpectraListInfo(BaseStructure):
    h5_type = "spectra list info"

    file_spectrum_info_list: List[SpectrumInfo] = Field(default_factory=list)

    selected_start_time: Optional[datetime] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NoiseFormulaParameter(BaseTableItem):
    item_name = "noise formula parameter"
    formula: Formula
    delta: float

    selected: bool
    param: Ndarray[float, (2, 3)]


def default_formula_parameter():
    return [NoiseFormulaParameter(
            formula=Formula(f), delta=5, selected=False, param=np.zeros((2, 3))) for f in config.noise_formulas]


class NoiseTabInfo(BaseStructure):
    h5_type = "noise tab"

    current_spectrum: Optional[Spectrum] = None
    noise_formulas: List[NoiseFormulaParameter] = Field(
        default_factory=default_formula_parameter)

    n_sigma: float = 0
    poly_coef: np.ndarray = np.empty(0)
    global_noise_std: float = 0
    noise: np.ndarray = np.empty(0)
    LOD: np.ndarray = np.empty(0)


class WorkSpace(H5File):
    def __init__(self, path: str = None) -> None:
        super().__init__(path)
        self.info: WorkspaceInfo = self["info"] if "info" in self else WorkspaceInfo(
        )

        self.spectra_list = self.visit_or_create_widget(
            "spectraList", SpectraListInfo)
        self.noise_tab = self.visit_or_create_widget("noise_tab", NoiseTabInfo)

        self.widgets: List[Widget] = [self.spectra_list]

    def save(self):
        self["info"] = self.info
        for widget in self.widgets:
            widget.save()

    def visit_or_create_widget(self, path: str, info_class: Type[T]) -> Widget[T]:
        if path in self:
            return Widget(self._obj[path], info_class)
        return Widget(self._obj.create_group(path), info_class)
