from typing import List

from ...utils.formula import Formula
from ..base import BaseStructure, BaseTableItem, Field


class Ion(BaseTableItem):
    item_name = "calibration ion"

    shown_text: str
    formula: Formula


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator"

    ions: List[Ion]=Field(default_factory=list)
