from copy import copy
from dataclasses import dataclass, field
from functools import lru_cache
import math
from typing import Dict, List, Tuple, Union
from pyteomics.mass import nist_mass
from .. import Formula


@lru_cache(None)
def get_num(key: str, num=0):
    return round(nist_mass[key][num][0])


@lru_cache(None)
def get_mass(key: str, num=0):
    return nist_mass[key][num][0]


@dataclass
class State:
    DBE2: float = 0
    OMin: float = 0
    OMax: float = 0
    HMin: float = 0
    HMax: float = 0

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
class IsotopeNum:
    element: str
    e_mass_num: int
    i_mass_num: int
    min: int
    max: int
    element_min: int
    element_max: int


@dataclass
class NumState:
    element: str
    current: int
    max: int
    e_current: int
    total_isotope_sum: int
    mass: float


@dataclass
class Calculator:
    rtol: float = 1e-6
    DBEMin: float = 0
    DBEMax: float = 8
    nitrogenRule: bool = False
    maxIsotope: int = 3
    limitedIsotope: bool = True
    relativeOH_DBE: bool = True
    element_states: Dict[str, State] = field(default_factory=dict)
    element_nums: List[IsotopeNum] = field(default_factory=list)
    debug: bool = True

    def get(self, M: float, e: int):
        delta = self.rtol * M
        RawM = M
        RawML = RawM - delta
        RawMR = RawM + delta
        M -= Formula(charge=e).mass()
        ML = M - delta
        MR = M + delta

        LEN = len(self.element_nums)
        cur = 0
        states: List[State] = [self.element_states["e"] * e]
        num_states: List[NumState] = [NumState()]
        formulas: List[Formula] = [Formula(charge=e)]

        while True:
            ns = num_states[cur]
            if ns.current > ns.max:
                cur -= 1
                if cur == 0:
                    break
                num_states.pop()
                states.pop()
                formulas.pop()

                ns = num_states[-1]
                s = states[-1]
                e_num = self.element_nums[cur - 1]
                e_s = self.element_states[e_num.element]
                ns.current += 1
                ns.mass += get_mass(e_num.element, e_num.i_mass_num)
                if self.limitedIsotope and e_num.e_mass_num != e_num.i_mass_num:
                    ns.total_isotope_sum += 1
                s += e_s
                formulas[-1][f"{e_num.element}{e_num.i_mass_num}"] += 1
            else:
                last_ns = num_states[-1]
                last_s = states[-1]
                last_f = formulas[-1]
                e_num = self.element_nums[cur]
                e_s = self.element_states[e_num.element]
                e_mass = get_mass(e_num.element, e_num.i_mass_num)
                mi = e_num.min
                if cur == LEN or self.element_nums[cur + 1].element != e_num.element:
                    if last_ns.element == e_num.element:
                        mi = max(mi, e_num.element_min - last_ns.e_current)
                    else:
                        mi = max(mi, e_num.element_min)
                    if self.relativeOH_DBE:
                        if e_num.element == "O":
                            mi = max(mi, last_s.OMin)
                        elif e_num.element == "H":
                            mi = max(
                                mi, last_s.HMin,
                                (self.DBEMax - last_s.DBE2) / e_s.DBE2)
                    if cur == LEN:
                        mi = max(mi, math.ceil((ML - last_ns.mass) / e_mass))

                ma = e_num.max
                if last_ns.element == e_num.element:
                    ma = min(ma, e_num.element_max - last_ns.e_current)
                    e_current = last_ns.e_current + mi
                else:
                    e_current = mi
                if self.relativeOH_DBE:
                    if e_num.element == "O":
                        ma = min(ma, last_s.OMax)
                    elif e_num.element == "H":
                        ma = min(ma, last_s.HMax)

                if self.limitedIsotope:
                    if e_num.e_mass_num != e_num.i_mass_num:
                        isotope_sum = last_ns.total_isotope_sum + mi
                        ma = min(ma, self.maxIsotope -
                                 last_ns.total_isotope_sum)
                    else:
                        isotope_sum = last_ns.total_isotope_sum
                ma = min(ma, math.floor((MR - last_ns.mass) / e_mass))

                key = f"{e_num.element}{e_num.i_mass_num}"
                f = copy(last_f)
                if cur != LEN:
                    ns = NumState(e_num.element, mi, ma, e_current, isotope_sum,
                                  last_ns.mass + mi * e_mass)
                    num_states.append(ns)
                    states.append(last_s + e_s * mi)
                    f[key] = mi
                    formulas.append(f)
                    cur += 1
                else:
                    if self.nitrogenRule:
                        for i in range(mi, ma):
                            DBE2 = last_s.DBE2 + i * e_s.DBE2
                            if abs(round(DBE2) - DBE2) < 1e-6:
                                f[key] = i
                                if self.check(f, RawML, RawMR):
                                    yield f
                            elif self.debug:
                                raise ValueError(str(f))
                    else:
                        for i in range(mi, ma):
                            f[key] = i
                            if self.check(f, RawML, RawMR):
                                yield f
                            elif self.debug:
                                raise ValueError(str(f))

    def check(self, f: Formula, ml: float, mr: float):
        if not ml <= f.mass() <= mr:
            return False
        s = State()
        o = f.findOrigin()
        for e, n in o.items():
            s += self.element_states[e] * n
        if not s.OMin <= 0 <= s.OMax:
            return False
        if not s.HMin <= 0 <= s.HMax:
            return False
        if not self.DBEMin <= s.DBE2 <= self.DBEMax:
            return False
        return True
