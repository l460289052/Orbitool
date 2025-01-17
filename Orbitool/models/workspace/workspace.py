from dataclasses import fields
from pathlib import Path
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union

from Orbitool.base import BaseDiskData, BaseStructure, DiskList, H5File
from Orbitool.base.structure import broken_entries

from ...version import VERSION
from ..spectrum import Spectrum
from ..timeseries import TimeSeries
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
    version: str = VERSION
    file_tab: FileTabInfo = FileTabInfo()
    noise_tab: NoiseTabInfo = NoiseTabInfo()
    peak_shape_tab: PeakShapeInfo = PeakShapeInfo()
    calibration_tab: CalibratorInfo = CalibratorInfo()
    peak_fit_tab: PeakFitInfo = PeakFitInfo()
    mass_defect_tab: MassDefectInfo = MassDefectInfo()
    time_series_tab: TimeseriesInfo = TimeseriesInfo()

    spectra_list: SpectraListInfo = SpectraListInfo()
    formula_docker: FormulaInfo = FormulaInfo()
    masslist_docker: MassListInfo = MassListInfo()
    # peaklist_docker: BaseStructure = field(BaseStructure)
    spectrum_docker: SpectrumInfo = SpectrumInfo()


class WorkspaceData(BaseDiskData):
    raw_spectra = DiskList(Spectrum)
    calibrated_spectra = DiskList(Spectrum)
    time_series = DiskList(TimeSeries)


class WorkSpace:
    def __init__(self, path: Union[str, Path, None] = None, use_proxy=True) -> None:
        if path is not None:
            path = Path(path)
        else:
            use_proxy = False
        self.use_proxy = use_proxy

        info = None
        if use_proxy:
            assert path is not None
            self.file = H5File(path, 'r')
            self.proxy_file = H5File(path.with_suffix(".orbt-temp"))
            if "info" in self.proxy_file:
                info = self.proxy_file.read("info", WorkspaceInfo)
            self.data = WorkspaceData(self.file.get_h5group("data"), self.proxy_file.get_h5group("data"))
        else:
            self.file = H5File(path, 'a')
            self.proxy_file = None
            self.data = WorkspaceData(self.file.get_h5group("data"))
        if info is None:
            if "info" in self.file:
                info = self.file.read("info", WorkspaceInfo)
            else:
                info = WorkspaceInfo()
        self.info = info

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
            self.data = WorkspaceData(self.file.get_h5group("data"), self.proxy_file.get_h5group("data"))
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
        if self.file._file and path.exists():
            assert not self.file._io.samefile(path), "please choose another destination"
        if path.exists():
            path.unlink()
        new_space = WorkSpace(path, False)
        new_space.info = self.info
        try:
            new_space.data.raw_spectra = self.data.raw_spectra
        except:
            broken_entries.append(new_space.data.raw_spectra.obj.name)
        try:
            new_space.data.calibrated_spectra = self.data.calibrated_spectra
        except:
            broken_entries.append(
                new_space.data.calibrated_spectra.obj.name)
        new_space.save()
        new_space.close()

        self.close()

    def load_config_from_file(self, f: str):
        file = H5File(f, 'r')
        info = file.read("info", WorkspaceInfo)
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
