from typing import Optional

from Orbitool.models.spectrum.spectrum import Spectrum

from .base import BaseInfo


class SpectrumInfo(BaseInfo):
    spectrum: Optional[Spectrum] = None
