from typing import Optional
from ..spectrum import Spectrum
from ..peakfit import PeaksManager, normal_distribution
from .base import BaseInfo


class PeakShapeInfo(BaseInfo):
    spectrum: Optional[Spectrum] = None

    peaks_manager: Optional[PeaksManager] = None
    func: Optional[normal_distribution.NormalDistributionFunc] = None
