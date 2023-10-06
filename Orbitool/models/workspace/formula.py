from typing import List

from pydantic import Field

from ..formula import CalculatorGenerator, Formula, ElementState, GenInitParams, IsotopeNum
from .base import BaseInfo


def Factory():
    ins = CalculatorGenerator(
        element_states={
            row[0]: ElementState.fromParam(row[1:]) for row in GenInitParams},
        isotope_usable={
            "C": IsotopeNum.init(12, 0, 0, 20, False),
            # "C[12]": IsotopeNum.init(12, 12, 0, 10, False),
            "C[13]": IsotopeNum.init(12, 13, 0, 3, True),
            "H": IsotopeNum.init(1, 0, 0, 40, False),
            "O": IsotopeNum.init(16, 0, 0, 15, False),
            "O[18]": IsotopeNum.init(16, 18, 0, 2, True),
            "N": IsotopeNum.init(14, 0, 0, 3, False)
        }
    )
    return ins


class FormulaInfo(BaseInfo):
    charge: int = -1
    mz_min: float = 50
    mz_max: float = 750
    calc_gen: CalculatorGenerator = Field(default_factory=Factory)

    def get_calcer(self):
        calc = self.calc_gen.generate()
        charge = self.charge

        def getter(mass: float) -> List[Formula]:
            return calc.get(mass, charge)
        return getter
