
from ..utils.formula import Formula, ForceCalc, RestrictedCalc
from ..structures.base import BaseStructure, Field


def RestrictedCalcFactory():
    calc = RestrictedCalc()
    calc.setEI('N')
    return calc


def ForceCalcFactory():
    calc = ForceCalc()
    calc['N'] = 999
    return calc


class FormulaInfo(BaseStructure):
    h5_type = "formula docker"

    polarity: int = -1
    mz_min: float = 50
    mz_max: float = 750
    rtol: float = 1e-6

    restricted_calc: RestrictedCalc = Field(
        default_factory=RestrictedCalcFactory)
    force_calc: ForceCalc = Field(default_factory=ForceCalcFactory)
