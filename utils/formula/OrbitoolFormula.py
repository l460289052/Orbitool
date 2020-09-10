# -*- coding: utf-8 -*-

from typing import Union

import numpy as np

from ._OrbitoolElement import setPara, getPara, getParas
from ._OrbitoolFormula import Formula

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
    def findOrigin(self):
        pass
    def DBE(self)->float:
        pass
    def toStr(self, showProton: bool = False, withCharge: bool = True)->str:
        pass
    def relativeAbundance(self):
        pass
    def clear(self):
        pass
    def to_numpy(self)->np.ndarray:
        pass
    @classmethod
    def from_numpy(cls, data: np.ndarray):
        pass
    def __setitem__(self, key: str, value: int):
        pass
    def __getitem__(self, key: str)->int:
        pass
    def __str__(self):
        pass
    def __repr__(self):
        pass
    def __copy__(self):
        pass
    def __iadd__(self, formula):
        pass
    def __add__(self, formula):
        pass
    def __isub__(self, formula):
        pass
    def __sub__(self, formula):
        pass
    def __imul__(self, times):
        pass
    def __mul__(self, times):
        pass
    def __eq__(self, formula):
        pass
    def __contains__(self, formula):
        '''
        f1 in f2
        '''
        pass
    def __hash__(self):
        pass