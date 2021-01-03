# -*- coding: utf-8 -*-
from typing import Union, List
from .formula import Formula, FormulaHint
from ._formulaCalc import IonCalculator, ForceCalculator

class IonCalculatorHint:
    def __init__(self):
        self.ppm: float = None
        self.charge: int = None
        self.DBEmin: float = None
        self.DBEmax: float = None
        self.Mmin: float = None
        self.Mmax: float = None
        self.nitrogenRule: bool = None
        
    def setEI(self, key: str, use: bool = True):
        pass
    def getElements(self) -> List[str]:
        pass
    def getIsotopes(self) -> List[str]:
        pass
    def calc(self):
        pass
    def get(self, M:float) -> List[FormulaHint]:
        pass
    def clear(self):
        pass

class ForceCalculatorHint:
    def __init__(self):
        self.ppm: float = None
        self.charge: int = None
    def __setitem__(self, key:str, value:int):
        pass
    def __getitem__(self, key:str)->int:
        pass
    def getEI(self) -> List[str]:
        pass
    def get(self, M: float) -> List[FormulaHint]:
        pass
