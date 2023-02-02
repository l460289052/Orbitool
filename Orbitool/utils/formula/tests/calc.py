from copy import copy
from dataclasses import dataclass
import math
from typing import Dict, Tuple
IntPair = Tuple[int, int]


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


class Calculator:
    def __init__(self) -> None:
        self.rtol = 1e-6
        self.DBEMin = 0
        self.DBEMax = 8
        self.MMin = 50
        self.MMax = 750
        self.nitrogenRule = False
        self.limited_isotope = True
        self.relative_OH = True

        self.element_states: Dict[str, State] = {
            row[0]: State(*row[2:]) for row in InitParams}
        self.element_usable: Dict[str, int] = {
            "C": 20,
            "H": 40,
            "O": 15}

    def setEI(self, key: str, num: int):
        if num:
            self.element_usable[key] = num
        else:
            if key in self.element_usable:
                del self.element_usable[key]

    def getEI(self, key:str):
        return self.element_usable.get(key, 0)


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
