from Orbitool.models.spectrum.spectrum import Spectrum
from Orbitool.structures import BaseStructure
from .base import BaseInfo


class SpectrumInfo(BaseInfo):
    h5_type = "spectrum docker"

    spectrum: Spectrum = None
