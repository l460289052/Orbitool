from typing import List, Union, Iterable
from ...structures import spectrum, HDF5, base, StructureTypeHandler, BaseStructure, Row
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


class PeaksManagerStructure(BaseStructure):
    h5_type = "peaks manager structure"
    peaks: Row[spectrum.FittedPeak]


class Handler(StructureTypeHandler):
    def write_to_h5(self, h5group, key: str, value: PeaksManager):
        struct = PeaksManagerStructure(peaks=value.peaks)
        handler: StructureTypeHandler = base.get_handler(PeaksManagerStructure)
        handler.write_to_h5(h5group, key, struct)

    def read_from_h5(self, h5group, key: str):
        handler: StructureTypeHandler = base.get_handler(PeaksManagerStructure)
        struct: PeaksManagerStructure = handler.read_from_h5(h5group, key)
        manager = PeaksManager(struct.peaks)
        return manager


base.register_handler(PeaksManager, Handler)
