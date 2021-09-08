
from ..utils.formula import Formula, ForceCalc, RestrictedCalc
from ..structures.base import BaseStructure, Field


def RestrictedCalcFactory():
    calc = RestrictedCalc()
    calc.setEI('N')
    calc.setEI('C[13]')
    calc.setEI('O[18]')
    return calc


def ForceCalcFactory():
    calc = ForceCalc()
    calc['C'] = 20
    calc['H'] = 40
    calc['C[13]'] = 3
    calc['O[18]'] = 3
    calc['N'] = 5
    return calc


class FormulaInfo(BaseStructure):
    h5_type = "formula docker"

    base_group: Formula = Formula("-")
    mz_min: float = 50
    mz_max: float = 750
    rtol: float = 1e-6

    restricted_calc: RestrictedCalc = Field(
        default_factory=RestrictedCalcFactory)
    force_calc: ForceCalc = Field(default_factory=ForceCalcFactory)

    def restricted_calc_get(self, M: float):
        return self.restricted_calc.get(M, self.base_group)

    def force_calc_get(self, M: float):
        return self.force_calc.get(M, self.base_group)
