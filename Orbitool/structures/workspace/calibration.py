from typing import List

from ...utils.formula import Formula
from ..base import BaseStructure, BaseTableItem, Field


class Ion(BaseTableItem):
    item_name = "calibration ion"

    shown_text: str
    formula: Formula


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator"

    ions: List[Ion] = Field(default_factory=list)

    def add_ions(self, ions: List[str]):
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            f = Formula(ion)
            if f in s:
                continue
            self.ions.append(Ion(shown_text=ion, formula=f))
