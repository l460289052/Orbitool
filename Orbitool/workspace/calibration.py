from typing import List, Dict

from ..functions.calibration import Ion, Calibrator, PolynomialRegressionFunc
from ..utils.formula import Formula
from ..structures.base import BaseStructure, BaseTableItem, Field
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..structures.HDF5 import StructureList
from .base import Widget as BaseWidget


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    ions: List[Ion] = Field(default_factory=list)
    calibrators: Dict[str, Calibrator] = Field(default_factory=dict)
    poly_funcs: Dict[str, PolynomialRegressionFunc] = Field(
        default_factory=dict)
    calibrated_spectrum_infos: List[SpectrumInfo] = Field(default_factory=list)

    def add_ions(self, ions: List[str]):
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            f = Formula(ion)
            if f in s:
                continue
            self.ions.append(Ion(shown_text=ion, formula=f))


class Widget(BaseWidget[CalibratorInfo]):
    raw_spectra = StructureList(Spectrum)  # should be move to file tab
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
