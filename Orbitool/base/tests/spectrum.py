from datetime import datetime

import numpy as np

from .. import NdArray
from ..structure import BaseStructure


class Spectrum(BaseStructure):
    mz: NdArray[float, -1] = None
    intensity: NdArray[float, -1] = None
    time: datetime = None

    def __eq__(self, another):
        if isinstance(another, Spectrum):
            return all(self.mz == another.mz) and all(self.intensity == another.intensity) and self.time == another.time
        return False
