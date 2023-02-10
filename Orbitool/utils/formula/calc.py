from copy import copy
from dataclasses import dataclass, field
from functools import lru_cache
import math
from typing import Dict, List, Tuple, Union
from pyteomics.mass import nist_mass
from . import Formula
from .calc_gen import State, CalcIsotopeNum


@lru_cache(None)
def get_mass(key: str, num=0):
    return nist_mass[key][num][0]


@dataclass
class NumState:
    element: str
    current: int
    max: int
    e_current: int
    global_limit_sum: int
    mass: float


@dataclass
class Calculator:
    rtol: float = 1e-6
    DBEMin: float = 0
    DBEMax: float = 8
    nitrogenRule: bool = True
    global_limit: int = 3
    relativeOH_DBE: bool = True
    H_max_mass: float = get_mass("H")
    element_states: Dict[str, State] = field(default_factory=dict)
    isotope_nums: List[CalcIsotopeNum] = field(default_factory=list)
    debug: bool = False

    def get(self, M: float, charge: int):
        delta = self.rtol * M
        ML = M - delta
        MR = M + delta

        TAIL = len(self.isotope_nums) - 1
        cur = 0
        states: List[State] = [self.element_states["e"]
                               * -charge - self.element_states["H"] * 2]
        num_states: List[NumState] = [
            NumState("e", -charge, -charge, -charge, 0, get_mass("e*") * -charge)]
        formulas: List[Formula] = [Formula(charge=charge)]

        while True:
            ns = num_states[-1]
            if ns.current <= ns.max:
                last_ns = num_states[-1]
                last_s = states[-1]
                last_f = formulas[-1]
                # print(last_f)
                e_num = self.isotope_nums[cur]
                e_s = self.element_states[e_num.element]
                e_mass = get_mass(e_num.element, e_num.i_num)
                mi = e_num.i_min
                if cur == TAIL or self.isotope_nums[cur + 1].element != e_num.element:
                    if last_ns.element == e_num.element:
                        mi = max(mi, e_num.e_min - last_ns.e_current)
                    else:
                        mi = max(mi, e_num.e_min)
                    if self.relativeOH_DBE:
                        if e_num.element == "O":
                            mi = max(mi, last_s.OMin, (ML - last_ns.mass -
                                     self.H_max_mass * last_s.HMax) / e_mass)
                        elif e_num.element == "H":
                            mi = max(
                                mi, last_s.HMin,
                                (self.DBEMax * 2 - last_s.DBE2) / e_s.DBE2)
                    if cur == TAIL:
                        mi = max(mi, (ML - last_ns.mass) / e_mass)
                mi = math.ceil(mi)

                ma = e_num.i_max
                if last_ns.element == e_num.element:
                    ma = min(ma, e_num.e_max - last_ns.e_current)
                    e_current = last_ns.e_current + mi
                else:
                    e_current = mi
                if self.relativeOH_DBE:
                    if e_num.element == "O":
                        ma = min(ma, last_s.OMax)
                    elif e_num.element == "H":
                        ma = min(ma, last_s.HMax,
                                 (self.DBEMin * 2 - last_s.DBE2) / e_s.DBE2)

                if e_num.global_limit:
                    global_limit_sum = last_ns.global_limit_sum + mi
                    ma = min(ma, self.global_limit -
                             last_ns.global_limit_sum)
                else:
                    global_limit_sum = last_ns.global_limit_sum
                ma = min(ma, (MR - last_ns.mass) / e_mass)
                ma = math.floor(ma)

                f = copy(last_f)
                if cur != TAIL:
                    ns = NumState(e_num.element, mi, ma, e_current, global_limit_sum,
                                  last_ns.mass + mi * e_mass)
                    num_states.append(ns)
                    states.append(last_s + e_s * mi)
                    f.addElement(e_num.element, e_num.i_num, mi)
                    formulas.append(f)
                    cur += 1
                    continue
                else:
                    f.addElement(e_num.element, e_num.i_num, mi)
                    if self.nitrogenRule:
                        DBE = (last_s.DBE2 + mi * e_s.DBE2) / 2.
                        for _ in range(mi, ma + 1):
                            if abs(round(DBE) - DBE) < 1e-6 and self.check(f, ML, MR, charge):
                                yield copy(f)
                            elif self.debug:
                                raise ValueError(str(f))
                            DBE += e_s.DBE2 / 2.
                            f.addElement(e_num.element, e_num.i_num)
                    else:
                        for _ in range(mi, ma + 1):
                            if self.check(f, ML, MR, charge):
                                yield copy(f)
                            elif self.debug:
                                raise ValueError(str(f))
                            f.addElement(e_num.element, e_num.i_num)
            else:
                cur -= 1
                if cur == 0:
                    break
                num_states.pop()
                states.pop()
                formulas.pop()

            ns = num_states[-1]
            s = states[-1]
            e_num = self.isotope_nums[cur - 1]
            e_s = self.element_states[e_num.element]
            ns.current += 1
            ns.e_current += 1
            ns.mass += get_mass(e_num.element, e_num.i_num)
            if e_num.global_limit:
                ns.global_limit_sum += 1
            s += e_s
            formulas[-1].addElement(e_num.element, e_num.i_num)

    def check(self, f: Formula, ml: float, mr: float, charge: float):
        if not ml <= f.mass() <= mr:
            return False
        if abs(f.charge - charge) > 1e-6:
            return False
        s: State = self.element_states["H"] * -2
        o = f.findOrigin()
        for e, n in o.items():
            s += self.element_states[e] * n
        if self.relativeOH_DBE:
            if not s.OMin <= 0 <= s.OMax:
                return False
            if not s.HMin <= 0 <= s.HMax:
                return False
            if not self.DBEMin <= s.DBE2 / 2 <= self.DBEMax:
                return False
        return True
