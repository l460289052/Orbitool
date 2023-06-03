from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple, Type, TypeVar, Union
from pyteomics.mass import nist_mass

from Orbitool.structures import BaseRowItem, field, BaseStructure, DictRow

from ._formula import Formula
from ._calc import Calculator

Isotope = Tuple[str, int]


class IsotopeNum(BaseRowItem):
    item_name = "IsotopeNum"

    e_num: int
    i_num: int
    min: int = 0
    max: int = 0
    global_limit: bool = False


class State(BaseRowItem):
    item_name = "ElementState"
    DBE2: float = 0
    HMin: float = 0
    HMax: float = 0
    OMin: float = 0
    OMax: float = 0

    def to_list(self):
        return [self.DBE2, self.HMin, self.HMax, self.OMin, self.OMax]

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


class CalcIsotopeNum(BaseRowItem):
    item_name = "CalcIsotopeNum"

    element: str
    e_num: int
    i_num: int
    global_limit: bool
    i_min: int
    i_max: int
    e_min: int
    e_max: int

    def __repr__(self) -> str:
        return f"IsotopeNum({self.element},{self.e_num},{self.i_num},{self.global_limit},{self.i_min},{self.i_max},{self.element_min},{self.element_max})"


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


# for Generator, Python is better than Cython
class CalculatorGenerator(BaseStructure):
    h5_type = "calculator generator"
    rtol: float = 1e-6
    DBEMin: float = 0
    DBEMax: float = 8
    nitrogen_rule: bool = True
    global_limit: int = 3
    dbe_limit: bool = True
    debug: bool = False
    element_states: DictRow[str, State] = field(dict)
    isotope_usable: DictRow[str, IsotopeNum] = field(dict)

    @classmethod
    def Factory(cls):
        ins = cls(
            element_states={
                row[0]: State(*row[1:]) for row in InitParams},
            isotope_usable={
                "C": IsotopeNum(12, 0, 0, 20, False),
                # "C[12]": IsotopeNum(12, 12, 0, 10, False),
                "H": IsotopeNum(1, 0, 0, 40, False),
                "O": IsotopeNum(16, 0, 0, 15, False),
                }
        )
        return ins

    def add_EI(self, key: str):
        if key in self.isotope_usable:
            return
        key1, key2 = parse_element(key)
        if key2 != 0:
            if key1 not in self.isotope_usable:
                self.add_EI(key1)
            e_num = self.isotope_usable[key1]
            i_num = copy(e_num)
            i_num.i_num = key2
            if i_num.e_num != key2:
                i_num.global_limit = True
            self.isotope_usable[key] = i_num
        else:
            self.isotope_usable[key] = IsotopeNum(get_num(key), 0, 0, 3, False)

    def del_EI(self, key: str):
        _ = parse_element(key)
        assert key in self.isotope_usable, f"Cannot find {key} in list"
        del self.isotope_usable[key]

    def get_E_iter(self):
        for k, v in self.isotope_usable.items():
            if v.i_num == 0:
                yield k, v

    def get_I_iter(self, e_num: int):
        for k, v in self.isotope_usable.items():
            if v.e_num == e_num and v.i_num != 0:
                yield k, v

    def get_EI_List(self):
        return self.isotope_usable.keys()

    def set_EI_num(self, key: str, min: int, max: int, global_limit: bool):
        assert key in self.isotope_usable, f"Isotope {key} should be added first"
        i_num = self.isotope_usable[key]
        _ = parse_element(key)
        assert min >= 0 and max >= 0, f"Isotope {key}'s min/max should be non-negative"
        assert not (
            i_num.i_num == 0 and global_limit), f"Cannot set global_limit to a whole element"
        self.isotope_usable[key] = IsotopeNum(
            i_num.e_num, i_num.i_num, min, max, global_limit)

    def get_EI_num(self, key: str):
        _ = parse_element(key)
        assert key in self.isotope_usable, f"Cannot find {key} in list"
        return self.isotope_usable[key]

    def generate(self, cls: Union[Type[Calculator], None] = None):
        if cls is None:
            from ._calc import Calculator
            cls = Calculator
        assert len(self.isotope_usable) >= 2, "At least two isotopes should be added"
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

        isotope_nums: List[CalcIsotopeNum] = []
        for key, num in e_list:
            isotope_nums.extend(e_to_list(key, num.e_num))

        if "O" in self.isotope_usable:
            isotope_nums.extend(e_to_list("O", get_num("O")))
        if "H" in self.isotope_usable:
            ret = e_to_list("H", get_num("H"))
            H_max_mass = max(r.i_num for r in ret)
            isotope_nums.extend(ret)
        else:
            H_max_mass = 0

        return cls(
            self.rtol, self.DBEMin, self.DBEMax, self.nitrogen_rule,
            self.global_limit, self.dbe_limit, H_max_mass,
            self.element_states, isotope_nums, self.debug)


InitParams = [
    ('e', -1, -1, -1, 0, 0),
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
