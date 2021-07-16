from typing import List, Dict

from ..functions.calibration import Ion, Calibrator, PolynomialRegressionFunc
from ..utils.formula import Formula
from ..structures.base import BaseStructure, BaseTableItem, Field
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..structures.HDF5 import StructureList
from .base import Widget as BaseWidget


def default_ions():
    return list(map(Ion.FactoryFromText,
                    ["HNO3NO3-", "C6H3O2NNO3-", "C6H5O3NNO3-",
                     "C6H4O5N2NO3-", "C8H12O10N2NO3-", "C10H17O10N3NO3-"]))


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    skip: bool = False

    ions: List[Ion] = Field(default_factory=default_ions)
    calibrators: Dict[str, Calibrator] = Field(default_factory=dict)
    poly_funcs: Dict[str, PolynomialRegressionFunc] = Field(
        default_factory=dict)
    calibrated_spectrum_infos: List[SpectrumInfo] = Field(default_factory=list)

    def add_ions(self, ions: List[str]):
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            i = Ion.FactoryFromText(ion)
            if i.formula in s:
                continue
            self.ions.append(i)


class Widget(BaseWidget[CalibratorInfo]):
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
