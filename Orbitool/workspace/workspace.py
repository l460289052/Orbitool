from dataclasses import fields
from pathlib import Path
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union

from .. import VERSION
from ..structures import BaseStructure, BaseRowItem, StructureTypeHandler, get_handler, field
from ..structures.HDF5 import H5File, H5Obj, h5_brokens, BaseDiskData, DiskDict, DiskList
from ..structures.spectrum import Spectrum
from .base import BaseInfo
from .calibration import CalibratorInfo
from .file_tab import FileTabInfo
from .formula import FormulaInfo
from .massdefect import MassDefectInfo
from .masslist import MassListInfo
from .noise_tab import NoiseTabInfo
from .peak_fit import PeakFitInfo
from .peak_shape import PeakShapeInfo
from .spectra_list import SpectraListInfo
from .spectrum import SpectrumInfo
from .timeseries import TimeseriesInfo

T = TypeVar("T")


class WorkspaceInfo(BaseStructure):
    h5_type = "workspace info"

    version: str = VERSION
    file_tab: FileTabInfo = field(FileTabInfo)
    noise_tab: NoiseTabInfo = field(NoiseTabInfo)
    peak_shape_tab: PeakShapeInfo = field(PeakShapeInfo)
    calibration_tab: CalibratorInfo = field(CalibratorInfo)
    peak_fit_tab: PeakFitInfo = field(PeakFitInfo)
    mass_defect_tab: MassDefectInfo = field(MassDefectInfo)
    time_series_tab: TimeseriesInfo = field(TimeseriesInfo)

    spectra_list: SpectraListInfo = field(SpectraListInfo)
    formula_docker: FormulaInfo = field(FormulaInfo)
    masslist_docker: MassListInfo = field(MassListInfo)
    peaklist_docker: BaseStructure = field(BaseStructure)
    spectrum_docker: SpectrumInfo = field(SpectrumInfo)


class WorkspaceData(BaseDiskData):
    raw_spectra = DiskList(Spectrum)
    calibrated_spectra = DiskList(Spectrum)


class WorkSpace:
    def __init__(self, path: Union[str, Path] = None, use_proxy=True) -> None:
        if path is not None:
            path = Path(path)
        else:
            use_proxy = False
        self.use_proxy = use_proxy

        self.info: WorkspaceInfo = None
        if use_proxy:
            self.file = H5File(path, 'r')
            self.proxy_file = H5File(path.with_suffix(".obtl-temp"))
            if "info" in self.proxy_file:
                self.info = self.proxy_file.read("info")
            self.data = WorkspaceData(
                self.file.get_h5group("data"),
                self.proxy_file.get_h5group("data"))
        else:
            self.file = H5File(path, 'a')
            self.proxy_file = None
            self.data = WorkspaceData(self.file.get_h5group("data"))
        if self.info is None:
            if "info" in self.file:
                self.info = self.file.read("info")
            else:
                self.info = WorkspaceInfo()

    def save(self):
        if self.use_proxy:
            self.file.close()

            file = H5File(self.file._io, 'a')
            file.write("info", self.info)
            data = WorkspaceData(file.get_h5group(
                "data"), self.proxy_file.get_h5group("data"))
            data.save_to_disk()
            file.close()
            self.proxy_file.close()
            self.proxy_file._io.unlink()

            self.file = H5File(self.file._io, 'r')
            self.proxy_file = H5File(self.proxy_file._io)
            self.data = WorkspaceData(self.file.get_h5group(
                "data"), self.proxy_file.get_h5group("data"))
        else:
            self.file.write("info", self.info)

    def in_memory(self):
        return not self.file._file

    def close(self):
        self.file.close()
        if self.proxy_file:
            self.proxy_file.write("info", self.info)
            self.proxy_file.close()

    def close_as(self, path):
        path = Path(path)
        if self.file._file:
            assert not self.file._io.samefile(
                path), "please choose another destination"
        if path.exists():
            path.unlink()
        new_space = WorkSpace(path, False)
        new_space.info = self.info
        try:
            new_space.data.raw_spectra = self.data.raw_spectra
        except:
            h5_brokens.append(new_space.data.raw_spectra.obj.name)
        try:
            new_space.data.calibrated_spectra = self.data.calibrated_spectra
        except:
            h5_brokens.append(
                new_space.data.calibrated_spectra.obj.name)
        new_space.save()
        new_space.close()

        self.close()

    def load_config_from_file(self, f: str):
        file = H5File(f, 'r')
        info = file.read("info")
        self._load_config(info)

    def load_config(self, another: 'WorkSpace'):
        self._load_config(another.info)

    def _load_config(self, another: WorkspaceInfo):
        info = self.info

        for field in fields(info):
            if issubclass(field.type, BaseInfo):
                a: BaseInfo = getattr(info, field.name)
                b: BaseInfo = getattr(another, field.name)
                a.ui_state = b.ui_state

        info.noise_tab.general_setting = another.noise_tab.general_setting
        info.calibration_tab.ions = another.calibration_tab.ions
        info.formula_docker = another.formula_docker
        info.masslist_docker = another.masslist_docker
