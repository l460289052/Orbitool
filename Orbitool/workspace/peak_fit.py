from typing import Optional, List

from ..structures.base import BaseStructure, Field
from ..structures.spectrum import Spectrum, FittedPeak, Peak


class PeakFitInfo(BaseStructure):
    h5_type = "peak fit tab"
    spectrum: Optional[Spectrum] = None
    raw_peaks: List[Peak] = Field(default_factory=list)
    peaks: List[FittedPeak] = Field(default_factory=list)
