from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple, Type, TypeVar, Union
from pyteomics.mass import nist_mass

from ._formula import Formula

Isotope = Tuple[str, int]


@dataclass
class IsotopeNum:
    e_num: int
    i_num: int
    min: int = 0
    max: int = 0
    global_limit: bool = False


@dataclass
class State:
    DBE2: float = 0
    HMin: float = 0
    HMax: float = 0
    OMin: float = 0
    OMax: float = 0

    def __imul__(self, num: int):
        assert isinstance(num, int)
        self.DBE2 *= num
        self.OMin *= num
        self.OMax *= num
        self.HMin *= num
        self.HMax *= num
        return self

    def __mul__(self, num: int):
        new_ins = copy(self)
        new_ins *= num
        return new_ins

    def __iadd__(self, other: "State"):
        assert isinstance(other, State)
        self.DBE2 += other.DBE2
        self.OMin += other.OMin
        self.OMax += other.OMax
        self.HMin += other.HMin
        self.HMax += other.HMax
        return self

    def __add__(self, other: "State"):
        new_ins = copy(self)
        new_ins += other
        return new_ins

    def __isub__(self, other: "State"):
        self += other * -1
        return self

    def __sub__(self, other: "State"):
        new_ins = copy(self)
        new_ins -= other
        return new_ins


@dataclass
class CalcIsotopeNum:
    element: str
    e_num: int
    i_num: int
    global_limit: bool
    i_min: int
    i_max: int
    e_min: int
    e_max: int

    def __repr__(self) -> str:
        return f"IsotopeNum({self.element},{self.e_num},{self.i_num},{self.global_limit},{self.min},{self.max},{self.element_min},{self.element_max})"


@lru_cache(None)
def get_num(key: str, num=0):
    return round(nist_mass[key][num][0])


def parse_element(key: str):
    try:
        f = Formula(key)  # for check
        i = list(f.items())
        assert len(i) == 1
        assert i[0][1] == 1
    except:
        raise ValueError(f"Wrong element {key}") from None

    ind = key.find('[')
    if ind > 0:
        return key[:ind], int(key[ind + 1:-1])
    else:
        return key, 0


T = TypeVar("T")


class CalculatorGenerator:  # for Generator, Python is better than Cython
    def __init__(self) -> None:
        self.rtol = 1e-6
        self.DBEMin = 0
        self.DBEMax = 8
        self.nitrogenRule = True
        self.globalLimit = 3
        self.relativeOH_DBE = True
        self.debug = False

        self.element_states: Dict[str, State] = {
            row[0]: State(*row[1:]) for row in InitParams}
        self.element_usable: Dict[str, IsotopeNum] = {
            "C": IsotopeNum(12, 0, 0, 20, False),
            "H": IsotopeNum(1, 0, 0, 40, False),
            "O": IsotopeNum(16, 0, 0, 15, False)}

    def add_EI(self, key: str):
        key1, key2 = parse_element(key)
        if key2 != 0:
            if key1 not in self.element_usable:
                self.add_EI(key1)
            e_num = self.element_usable[key1]
            i_num = copy(e_num)
            i_num.i_num = key2
            if i_num.e_num != key2:
                i_num.global_limit = True
            self.element_usable[key] = i_num
        else:
            self.element_usable[key] = IsotopeNum(get_num(key), 0, 0, 3, False)

    def del_EI(self, key: str):
        _ = parse_element(key)
        assert key in self.element_usable, f"Cannot find {key} in list"
        del self.element_usable[key]

    def get_E_iter(self):
        for k, v in self.element_usable.items():
            if v.i_num == 0:
                yield k, v

    def get_I_iter(self, e_num: int):
        for k, v in self.element_usable.items():
            if v.e_num == e_num and v.i_num != 0:
                yield k, v

    def get_EI_List(self):
        return self.element_usable.keys()

    def set_EI_num(self, key: str, min: int, max: int, global_limit: bool):
        assert key in self.element_usable, f"Isotope {key} should be added first"
        i_num = self.element_usable[key]
        _ = parse_element(key)
        assert min >= 0 and max >= 0, f"Isotope {key}'s min/max should be non-negative"
        assert not (
            i_num.i_num == 0 and global_limit), f"Cannot set global_limit to a whole element"
        self.element_usable[key] = IsotopeNum(
            i_num.e_num, i_num.i_num, min, max, global_limit)

    def get_EI_num(self, key: str):
        _ = parse_element(key)
        assert key in self.element_usable, f"Cannot find {key} in list"
        return self.element_usable[key]

    def generate(self, cls: Type[T]=None) -> T:
        if cls is None:
            from ._calc import Calculator
            cls = Calculator
        e_list = [(k, v) for k, v in self.get_E_iter() if k not in "HO"]
        e_list.sort(key=lambda i: i[1].e_num, reverse=True)

        def e_to_list(e: str, e_mass_num: int):
            """
            stable isotope is the last
            """
            ret: List[CalcIsotopeNum] = []
            no_isotope: List[CalcIsotopeNum] = []
            flag = False
            e_num = self.get_EI_num(e)
            for _, i_num in self.get_I_iter(e_mass_num):
                i_mass_num = i_num.i_num
                if i_mass_num == e_mass_num:
                    flag = True
                if i_num.max == 0:
                    continue
                (ret if i_num.global_limit else no_isotope).append(
                    CalcIsotopeNum(
                        e, e_mass_num, i_mass_num, i_num.global_limit, i_num.min, i_num.max, e_num.min, e_num.max))
            ret.extend(no_isotope)
            if not flag:
                i_num = CalcIsotopeNum(
                    e, e_mass_num, e_mass_num, False, 0, e_num.max, e_num.min, e_num.max)
                ret.append(i_num)
            return ret

        element_nums: List[CalcIsotopeNum] = []
        for key, num in e_list:
            element_nums.extend(e_to_list(key, num.e_num))

        if "O" in self.element_usable:
            element_nums.extend(e_to_list("O", get_num("O")))
        if "H" in self.element_usable:
            ret = e_to_list("H", get_num("H"))
            H_max_mass = max(r.i_num for r in ret)
            element_nums.extend(ret)

        return cls(
            self.rtol, self.DBEMin, self.DBEMax, self.nitrogenRule,
            self.globalLimit, self.relativeOH_DBE, H_max_mass,
            self.element_states, element_nums, self.debug)


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
