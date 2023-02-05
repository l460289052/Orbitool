from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from tkinter import W
from typing import Dict, List, Tuple, Union
from pyteomics.mass import nist_mass
from .calc import Calculator, State, IsotopeNum as CalcIsotopeNum, get_num

Isotope = Tuple[str, int]


@dataclass
class IsotopeNum:
    min: int = 0
    max: int = 0


class CalculatorGenerator:  # for Generator, Python is better than Cython
    def __init__(self) -> None:
        self.rtol = 1e-6
        self.DBEMin = 0
        self.DBEMax = 8
        self.nitrogenRule = False
        self.maxIsotope = 3
        self.limitedIsotope = True
        self.relativeOH = True

        self.element_states: Dict[str, State] = {
            row[0]: State(*row[1:]) for row in InitParams}
        self.element_usable: Dict[str, Dict[int, IsotopeNum]] = {
            "C": {0: IsotopeNum(0, 20)},
            "H": {0: IsotopeNum(0, 40)},
            "O": {0: IsotopeNum(0, 15)}}

    def set_E_custom(self, key: str, enable: bool):
        d = self.element_usable.get(key, None)
        assert d, f"Please insert element '{key}' first"
        num = get_num(key)
        if enable and num not in d:
            d[num] = copy(d[0])
        if not enable and num in d:
            del d[num]
    
    def get_E_custom(self, key: str):
        d = self.element_usable.get(key, None)
        if not d:
            return None
        num = get_num(key)
        return d.get(num, None)

    def set_EI(self, key: Union[Isotope, str], min: int, max: int):
        if isinstance(key, str):
            key1 = key
            key2 = 0
        else:
            key1, key2 = key
        assert key1 in nist_mass
        assert min >= 0
        num = get_num(key1)
        assert num == key2 or max > 0
        if not key2:
            self.element_usable.setdefault(key1, {})[key2] = IsotopeNum(min, max)
        else:
            self.element_usable[key1][key2] = IsotopeNum(min, max)

    def del_EI(self, key: Union[Isotope, str]):
        if isinstance(key, str):
            key1 = key
            key2 = 0
        else:
            key1, key2 = key
        if key1 not in self.element_usable:
            return
        if not key2:
            del self.element_usable[key1]
        else:
            del self.element_usable[key1][key2]

    def get_EI(self, key: Isotope):
        if key[0] not in self.element_usable:
            return IsotopeNum()
        return self.element_usable.get(key[0]).get(key[1], IsotopeNum())

    def get_E_List(self):
        return self.element_usable.keys()

    def get_I_of_E(self, key: str) -> List[int]:
        if key in self.element_usable:
            return self.element_usable[key].keys()
        return []

    def generate(self):
        d = self.element_usable.copy()
        O = d.pop("O", None)
        H = d.pop("H", None)

        def e_to_list(e: str, v: Dict[int, IsotopeNum]):
            """
            stable isotope is the last
            """
            v = v.copy()
            e_num = v.pop(0)
            e_mass_num: int = get_num(e)
            ret = []
            for mass_num, num in v.items():
                if mass_num == e_mass_num:
                    continue
                ret.append(CalcIsotopeNum(
                    e, e_mass_num, mass_num, num.min, num.max, e_num.min, e_num.max))
            i_num = CalcIsotopeNum(
                    e, e_mass_num, e_mass_num, e_num.min, e_num.max, e_num.min, e_num.max)
            if (num:=v.get(e_mass_num, None)) is not None:
                if num.max == 0:
                    return ret
                i_num.min = num.min
                i_num.max = num.max
            ret.append(i_num)
            return ret

        element_nums: List[CalcIsotopeNum] = []
        for k, v in sorted(d.items(), key=lambda i:get_num(i[0]), reverse=True):
            element_nums.extend(e_to_list(k, v))

        if O is not None:
            element_nums.extend(e_to_list("O", O))
        if H is not None:
            element_nums.extend(e_to_list("H", H))
        
        return Calculator(
            self.rtol, self.DBEMin, self.DBEMax, self.nitrogenRule,
            self.maxIsotope, self.limitedIsotope, self.relativeOH,
            self.element_states, element_nums)


InitParams = [
    ('e', -1, -0.5, -0.5, 0, 0),
    ('C', 2, 0, 2, 0, 3),
    ('H', -1, -1, -1, 0, 0),
    ('O', 0, 0, 0, -1, -1),
    ('N', 1, -1, 1, 0, 3),
    ('S', 0, 0, 0, 0, 4),
    ('Li', -1, 0, 0, 0, 0),
    ('Na', -1, 0, 0, 0, 0),
    ('K', -1, 0, 0, 0, 0),
    ('F', -1, -1, 0, 0, 0),
    ('Cl', -1, -1, 0, 0, 3),
    ('Br', -1, -1, 0, 0, 3),
    ('I', -1, -1, 0, 0, 3),
    ('P', 1, -1, 1, 0, 6),
    ('Si', 2, 0, 2, 0, 3)]
