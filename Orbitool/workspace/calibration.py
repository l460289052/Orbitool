from typing import List, Dict
import math

from ..functions.calibration import Ion, Calibrator, PolynomialRegressionFunc
from ..utils.formula import Formula
from ..structures import BaseStructure, BaseRowItem, field, Row
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..structures.HDF5 import StructureList
from .base import Widget as BaseWidget


def default_ions():
    return list(map(Ion.fromText,
                    ["HNO3NO3-", "C6H3O2NNO3-", "C6H5O3NNO3-",
                     "C6H4O5N2NO3-", "C8H12O10N2NO3-", "C10H17O10N3NO3-"]))


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    skip: bool = False

    rtol: float = math.inf
    ions: Row[Ion] = field(default_ions)
    calibrators: Dict[str, Calibrator] = field(dict)
    poly_funcs: Dict[str, PolynomialRegressionFunc] = field(dict)
    calibrated_spectrum_infos: Row[SpectrumInfo] = field(list)

    def add_ions(self, ions: List[str]):
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            i = Ion.fromText(ion)
            if i.formula in s:
                continue
            self.ions.append(i)
        self.ions.sort(key=lambda ion: ion.formula.mass())


class Widget(BaseWidget[CalibratorInfo]):
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
