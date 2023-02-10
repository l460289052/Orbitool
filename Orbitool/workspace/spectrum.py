from Orbitool.structures.spectrum import Spectrum
from Orbitool.structures import BaseStructure


class SpectrumInfo(BaseStructure):
    h5_type = "spectrum docker"

    spectrum: Spectrum = None
