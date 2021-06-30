from ..base import BaseStructure
from ..spectrum import Spectrum, FittedPeak
from ...functions import peakfit


class PeakShapeInfo(BaseStructure):
    h5_type = "peak shape tab"

    spectrum: Spectrum = None

    peaks_manager: peakfit.PeaksManager = None
    func: peakfit.normal_distribution.NormalDistributionFunc = None
