
from ..utils.formula import Formula, ForceCalc, RestrictedCalc
from ..structures.base import BaseStructure, Field


def RestrictedCalcFactory():
    calc = RestrictedCalc()
    calc.setEI('N')


def ForceCalcFactory():
    calc = ForceCalc()
    calc['N'] = 999


class FormulaInfo(BaseStructure):
    h5_type = "formula docker"

    restricted_calc: RestrictedCalc = Field(
        default_factory=RestrictedCalcFactory)
    force_calc: ForceCalc = Field(default_factory=ForceCalcFactory)
