from ..base import BaseStructure
from..spectrum import Spectrum


class PeakShapeInfo(BaseStructure):
    h5_type = "peak shape tab"

    spectrum: Spectrum = None
