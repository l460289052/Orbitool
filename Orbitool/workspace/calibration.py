from typing import List, Dict

from ..functions.calibration import Ion, Calibrator, PolynomialRegressionFunc
from ..utils.formula import Formula
from ..structures.base import BaseStructure, BaseTableItem, Field


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    ions: List[Ion] = Field(default_factory=list)
    calibrators: Dict[str, Calibrator] = Field(default_factory=dict)
    poly_funcs: Dict[str, PolynomialRegressionFunc] = Field(
        default_factory=dict)

    def add_ions(self, ions: List[str]):
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            f = Formula(ion)
            if f in s:
                continue
            self.ions.append(Ion(shown_text=ion, formula=f))
