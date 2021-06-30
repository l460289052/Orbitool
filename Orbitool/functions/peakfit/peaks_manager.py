from typing import List, Union, Iterable
from ...structures import spectrum, HDF5, base
import numpy as np


class PeaksManager:
    def __init__(self, peaks: List[spectrum.FittedPeak]) -> None:
        self.peaks = peaks
        self.canceled: List[List[spectrum.FittedPeak]] = []

    def rm(self, index: Union[int, List[int]]):
        indexes = index if isinstance(index, Iterable) else (index,)
        indexes = np.unique(indexes)[::-1]
        removed = []
        for i in indexes:
            removed.append(self.peaks.pop(i))
        self.canceled.append(removed)

    def cancel(self) -> List[spectrum.FittedPeak]:
        if not self.canceled:
            return []
        removed = self.canceled.pop()
        for peak in removed:
            self.peaks.append(peak)
        return removed


class PeaksManagerStructure(base.BaseStructure):
    h5_type = "peaks manager structure"
    peaks: List[spectrum.FittedPeak]


class Conveter(HDF5.BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group, key: str, value: PeaksManager):
        struct = PeaksManagerStructure(peaks=value.peaks)
        HDF5.StructureConverter.write_to_h5(h5group, key, struct)

    @staticmethod
    def read_from_h5(h5group, key: str):
        struct: PeaksManagerStructure = HDF5.StructureConverter.read_from_h5(
            h5group, key)
        manager = PeaksManager(struct.peaks)
        return manager


HDF5.register_converter(PeaksManager, PeaksManagerStructure)
