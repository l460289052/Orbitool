# -*- coding: utf-8 -*-

from typing import Union

from _OrbitoolElement import setPara, getPara, getParas
from _OrbitoolFormula import Formula

class FormulaHint:
    def __init__(self, formula: Union[str, dict] = None, **kwargs):
        pass
    @property
    def charge(self)->int:
        pass
    @charge.setter
    def charge(self, value: int):
        pass
    @property
    def isIsotope(self)->bool:
        pass
    def mass(self)->float:
        pass
    def DBE(self)->float:
        pass
    def toStr(self, showProton: bool = False, withCharge: bool = True)->str:
        pass
    def relativeAbundance(self):
        pass
    def __setitem__(self, key: str, value: int):
        pass
    def __getitem__(self, key: str)->int:
        pass
    def __str__(self):
        pass
    def __repr__(self):
        pass
    def __eq__(self, formula):
        pass
    def __hash__(self):
        pass