from typing import List
from Orbitool.utils.formula.calc_gen import CalculatorGenerator
from ..utils.formula import Formula, CalculatorGenerator
from ..structures import BaseStructure, field


class FormulaInfo(BaseStructure):
    h5_type = "formula docker"

    charge: float = -1
    mz_min: float = 50
    mz_max: float = 750
    calc_gen: CalculatorGenerator = field(CalculatorGenerator.Factory)

    def get_calcer(self):
        calc = self.calc_gen.generate()
        charge = self.charge

        def getter(mass: float) -> List[Formula]:
            calc.get(mass, charge)
        return getter
