from ..structures import BaseStructure
from ..structures.spectrum import Spectrum, FittedPeak
from ..functions import peakfit
from ..functions.peakfit import normal_distribution
from .base import BaseInfo


class PeakShapeInfo(BaseInfo):
    h5_type = "peak shape tab"

    spectrum: Spectrum = None

    peaks_manager: peakfit.PeaksManager = None
    func: normal_distribution.NormalDistributionFunc = None
