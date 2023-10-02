from ..spectrum import Spectrum
from ..peakfit import PeaksManager, normal_distribution
from .base import BaseInfo


class PeakShapeInfo(BaseInfo):
    h5_type = "peak shape tab"

    spectrum: Spectrum = None

    peaks_manager: PeaksManager = None
    func: normal_distribution.NormalDistributionFunc = None
