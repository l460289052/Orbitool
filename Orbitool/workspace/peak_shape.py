from typing import Optional
from ..structures.base import BaseStructure
from ..structures.spectrum import Spectrum, FittedPeak
from ..functions import peakfit


class PeakShapeInfo(BaseStructure):
    h5_type = "peak shape tab"

    spectrum: Optional[Spectrum] = None

    peaks_manager: Optional[peakfit.PeaksManager] = None
    func: Optional[peakfit.normal_distribution.NormalDistributionFunc] = None
