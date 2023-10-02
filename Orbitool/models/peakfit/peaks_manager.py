from typing import List, Union, Iterable

from Orbitool.base import BaseStructure
from ...models.spectrum import spectrum
import numpy as np


class PeaksManager(BaseStructure):
    peaks: List[spectrum.FittedPeak]
    canceled: List[List[spectrum.FittedPeak]]

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
