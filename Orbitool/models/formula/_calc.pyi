from typing import Dict, List
from ._formula import Formula
from .calc_gen import State, CalcIsotopeNum


class Calculator:
    def __init__(
        self, rtol: float, DBEMin: float, DBEMax: float,
        nitrogen_rule: bool, global_limit: int, dbe_limit: bool,
        H_max_mass: float, element_states: Dict[str, State],
        element_nums: List[CalcIsotopeNum]) -> None: ...

    def get(self, M:float, charge:int)->List[Formula]:...
    def check(self, f:Formula, ml:float, mr:float, charge:float)->bool:...
