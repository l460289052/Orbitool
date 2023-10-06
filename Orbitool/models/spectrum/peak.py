from enum import Enum
from functools import cached_property
from typing import Any, Dict, Generic, Iterable, List, TypeVar, Union, cast
from h5py import Group as H5Group

import numpy as np

from Orbitool.base import (AttrNdArray, BaseDatasetStructure, BaseRowStructure,
                           BaseStructure)
from Orbitool.base.extra_type_handlers import NdArray
from Orbitool.base.structure import GroupTypeHandler, get_handler

from ..formula import Formula, FormulaList


class PeakTags(str, Enum):
    Noise = 'N'
    Done = 'D'
    Fail = 'F'


class Peak(BaseRowStructure):
    mz: NdArray[float, -1]
    intensity: NdArray[float, -1]

    @classmethod
    def h5_rows_handler(cls) -> GroupTypeHandler:
        return PeaksTypeHandler

    @classmethod
    def h5_storage_type(cls):
        return StoragePeak

    @cached_property
    def maxIntensity(self):
        return self.intensity.max()

    @cached_property
    def isPeak(self):
        return functions.getPeaksPositions(self.intensity)

    @cached_property
    def idPeak(self):
        return np.where(self.isPeak)[0]

    def to_storage(self, start_index: int, stop_index: int):
        return StoragePeak(start_index=start_index, stop_index=stop_index)


class StoragePeak(BaseRowStructure):
    """
      to cut from mz, intensity
      mz[self.start_index, self.stop_index]
    """
    start_index: int
    stop_index: int

    def to_peak(self, mz: np.ndarray, intensity: np.ndarray):
        return Peak(
            mz=mz[self.start_index: self.stop_index],
            intensity=intensity[self.start_index: self.stop_index]
        )


class FittedPeak(Peak):
    fitted_param: AttrNdArray[float, -1]
    peak_position: float
    peak_intensity: float
    area: float

    tags: str = ""
    formulas: FormulaList = []

    @classmethod
    def h5_storage_type(cls):
        return StorageFittedPeak

    def to_storage(self, start_index: int, stop_index: int):
        return StorageFittedPeak(
            start_index=start_index, stop_index=stop_index,
            fitted_param=self.fitted_param.tobytes(),
            peak_position=self.peak_position, peak_intensity=self.peak_intensity,
            area=self.area, tags=self.tags, formulas=self.formulas
        )


class StorageMzIntensity(BaseDatasetStructure):
    mz: NdArray[float, -1]
    intensity: NdArray[float, -1]


class StorageFittedPeak(StoragePeak):
    fitted_param: bytes
    peak_position: float
    peak_intensity: float
    area: float

    tags: str
    formulas: str

    def to_peak(self, mz: np.ndarray, intensity: np.ndarray):
        return FittedPeak(
            mz=mz[self.start_index:self.stop_index],
            intensity=intensity[self.start_index:self.stop_index],
            fitted_param=np.frombuffer(self.fitted_param, float),
            peak_position=self.peak_position, peak_intensity=self.peak_intensity,
            area=self.area, tags=self.tags, formulas=self.formulas

        )


class PeaksTypeHandler(GroupTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.data_handler = get_handler(StorageMzIntensity)
        inner_type: Peak
        storage_type: StoragePeak
        if self.origin == list:
            inner_type = self.args[0]
            storage_type = inner_type.h5_storage_type()
            peaks_handler = get_handler(List[storage_type])
        elif self.origin == dict:
            inner_type = self.args[1]
            storage_type = inner_type.h5_storage_type()
            peaks_handler = get_handler(Dict[self.args[0], storage_type])
        self.peaks_handler = peaks_handler

    def write_group_to_h5(self, group: H5Group, value: Union[List[Peak], Dict[Any, Peak]]):
        if self.origin == list:
            it = value
        elif self.origin == dict:
            it = value.values()
        else:
            assert False
        it: Iterable[Peak]
        ind = 0
        mz = []
        intensity = []
        peaks: List[StoragePeak] = []
        for peak in it:
            mz.append(peak.mz)
            intensity.append(peak.intensity)
            length = len(peak.mz)
            peaks.append(peak.to_storage(ind, ind + length))
            ind += length

        smi = StorageMzIntensity(
            mz=np.concatenate(mz, dtype=float),
            intensity=np.concatenate(intensity, dtype=float))

        self.data_handler.write_to_h5(group, "spectrum", smi)

        if self.origin == list:
            self.peaks_handler.write_to_h5(group, "peaks", peaks)
        elif self.origin == dict:
            self.peaks_handler.write_to_h5(
                group, "peaks", dict(zip(value.keys(), peaks)))

    def read_group_from_h5(self, group: H5Group) -> Any:
        smi: StorageMzIntensity = self.data_handler.read_from_h5(
            group, "spectrum")
        value = self.peaks_handler.read_from_h5(group, "peaks")
        if self.origin == list:
            value: List[StoragePeak]
            it = value
        elif self.origin == dict:
            value: Dict[Any, StoragePeak]
            it = value.values()
        it = cast(Iterable[StoragePeak], it)
        mz = smi.mz
        intensity = smi.intensity
        peaks = [peak.to_peak(mz, intensity) for peak in it]

        if self.origin == list:
            return peaks
        elif self.origin == dict:
            return dict(zip(value.keys(), peaks))


from . import functions  # avoid circular import
