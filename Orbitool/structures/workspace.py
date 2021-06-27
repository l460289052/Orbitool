from typing import Generic, List, Type, TypeVar, Union

from pydantic import BaseModel, Field

from ..utils import readers
from ..utils.formula import Formula
from .base import BaseStructure
from .file import FileList, SpectrumInfo, setFileReader
from .HDF5 import H5File, H5Obj

setFileReader(readers.ThermoFile)

T = TypeVar("T")


class Widget(H5Obj, Generic[T]):
    def __init__(self, obj, info_class: Type[T]) -> None:
        super().__init__(obj)
        self._info_class = info_class
        self.info: T = self["info"] if "info" in self else info_class()

    def save(self):
        self["info"] = self.info


# class SpectraList(H5Obj):
#     h5_type = HDF5.RegisterType("SpectraList")

#     file_spectrum_info_list = HDF5.datatable.Datatable.descriptor(SpectrumInfo)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.selected_start_time: datetime = None


# class NoiseFormulaParameter(HDF5.datatable.DatatableItem):
#     item_name = "NoiseFormulaParameter"
#     formula: Formula = FormulaDatatableDescriptor()
#     delta: float = HDF5.datatable.Float64()

#     selected: bool = HDF5.datatable.Bool()
#     param = HDF5.datatable.Ndarray2D(float, 3)


# class NoiseTab(HDF5.Group):
#     h5_type = HDF5.RegisterType("NoiseTab")

#     current_spectrum: spectrum.Spectrum = spectrum.Spectrum.descriptor()
#     noise_formulas = HDF5.datatable.Datatable.descriptor(NoiseFormulaParameter)

#     n_sigma = HDF5.Float()
#     poly_coef = HDF5.SimpleDataset()
#     global_noise_std = HDF5.Float()
#     noise = HDF5.SimpleDataset()
#     LOD = HDF5.SimpleDataset()

#     def initialize(self):
#         self.noise_formulas.initialize()

#         self.noise_formulas.extend([NoiseFormulaParameter(
#             Formula(f), 5, False, np.zeros((2, 3))) for f in config.noise_formulas])

class WorkspaceInfo(BaseStructure):
    h5_type = "workspace info"

    filelist: FileList = Field(default_factory=FileList)


class WorkSpace(H5File):
    def __init__(self, path: str = None) -> None:
        super().__init__(path)
        self.info: WorkspaceInfo = self["info"] if "info" in self else WorkspaceInfo()

        # self.spectra_list = self.visit_or_create("spectraList", )
        # self.noise_formula_parameter = self.visit_or_create(
        #     "noise_formula_parameter")
        # self.noise_tab = self.visit_or_create("noise_tab")

        # self.widgets = [self.spectra_list,
        #                 self.noise_formula_parameter, self.noise_tab]
        self.widgets: List[Widget] = []  # [self.spectra_list]

    def save(self):
        self["info"] = self.info
        for widget in self.widgets:
            widget.save()

    def visit_or_create_widget(self, path: str, info_class: Type[T]) -> Widget[T]:
        if path in self:
            return Widget(self._obj[path], info_class)
        return Widget(self._obj.create_group(path), info_class)
