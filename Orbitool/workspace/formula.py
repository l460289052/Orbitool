from typing import List

from ..utils.formula.calc_gen import CalculatorGenerator, State, InitParams, IsotopeNum
from ..utils.formula import Formula
from ..structures import BaseStructure, field
from .base import BaseInfo

def Factory():
    ins = CalculatorGenerator(
        element_states={
            row[0]: State(*row[1:]) for row in InitParams},
        isotope_usable={
            "C": IsotopeNum(12, 0, 0, 20, False),
            # "C[12]": IsotopeNum(12, 12, 0, 10, False),
            "C[13]": IsotopeNum(12, 13, 0, 3, True),
            "H": IsotopeNum(1, 0, 0, 40, False),
            "O": IsotopeNum(16, 0, 0, 15, False),
            "O[18]": IsotopeNum(16, 18, 0, 2, True),
            "N": IsotopeNum(14, 0, 0, 3, False)
            }
    )
    return ins

class FormulaInfo(BaseInfo):
    h5_type = "formula docker"

    charge: float = -1
    mz_min: float = 50
    mz_max: float = 750
    calc_gen: CalculatorGenerator = field(Factory)

    def get_calcer(self):
        calc = self.calc_gen.generate()
        charge = self.charge

        def getter(mass: float) -> List[Formula]:
            return calc.get(mass, charge)
        return getter
