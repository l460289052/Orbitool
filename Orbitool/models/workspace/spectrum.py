from Orbitool.models.spectrum.spectrum import Spectrum
from .base import BaseInfo


class SpectrumInfo(BaseInfo):
    spectrum: Spectrum = None
