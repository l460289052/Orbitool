
from ..utils.formula import Formula, ForceCalc, RestrictedCalc
from ..structures.base import BaseStructure, Field


class FormulaInfo(BaseStructure):
    h5_type = "formula docker"

    restricted_calc: RestrictedCalc = Field(default_factory=RestrictedCalc)
    force_calc: ForceCalc = Field(default_factory=ForceCalc)
