from functools import lru_cache
from itertools import chain
from typing import List

import numpy as np
from h5py import Group

from ...structures import (BaseRowItem, BaseStructure, RowDTypeHandler,
                           StructureTypeHandler, get_handler, register_handler)
from ...structures.HDF5 import AsciiLimit, Row
from ...structures.HDF5.h5type_handlers import AttrHandler, StrHandler
from ._forceCalc import Calculator as ForceCalc
from ._formula import Formula
from ._restrictedCalc import Calculator as RestrictedCalc


class FormulaHandler(StrHandler):
    def __call__(self, value) -> Formula:
        return Formula(value)

    def validate(self, value):
        if isinstance(value, Formula):
            return value
        return Formula(value)

    def write_to_h5(self, h5group: Group, key: str, value):
        h5group.attrs[key] = str(value)

    def read_from_h5(self, h5group: Group, key: str):
        return Formula(h5group.attrs[key])

    def convert_to_h5(self, value):
        return super().convert_to_h5(str(value))

    def convert_from_h5(self, value):
        return Formula(super().convert_from_h5(value))


class RestrictedCalcElementNumItem(BaseRowItem):
    item_name = "restriced cac formula num"

    element: AsciiLimit[10]
    Min: int
    Max: int
    DBE2: float
    HMin: float
    HMax: float
    OMin: float
    OMax: float

    def get_params(self):
        return {"Min": self.Min, "Max": self.Max, "DBE2": self.DBE2, "HMin": self.HMin, "HMax": self.HMax, "OMin": self.OMin, "OMax": self.OMax}


class RestrictedCalcStructure(BaseStructure):
    h5_type = "restricted calc"

    rtol: float
    DBEMin: float
    DBEMax: float
    MMin: float
    MMax: float
    nitrogenRule: bool

    params: Row[RestrictedCalcElementNumItem]
    elements: str
    isotopes: str


class RestrictedCalcHandler(StructureTypeHandler):
    def write_to_h5(self, h5group: Group, key: str, value: RestrictedCalc):
        parameters = [RestrictedCalcElementNumItem(e, **value[e])
                      for e in value.getInitedElements()]
        elements = ','.join(value.getElements())
        isotopes = ','.join(value.getIsotopes())
        struct = RestrictedCalcStructure(
            value.rtol, value.DBEMin, value.DBEMax,
            value.MMin, value.MMax, value.nitrogenRule,
            parameters, elements, isotopes)
        handler: StructureTypeHandler = get_handler(BaseStructure)
        handler.write_to_h5(h5group, key, struct)

    def read_from_h5(self, h5group: Group, key: str):
        handler: StructureTypeHandler = get_handler(BaseStructure)
        struct: RestrictedCalcStructure = handler.read_from_h5(h5group, key)
        calc = RestrictedCalc()

        calc.rtol = struct.rtol
        calc.DBEMin = struct.DBEMin
        calc.DBEMax = struct.DBEMax
        calc.MMin = struct.MMin
        calc.MMax = struct.MMax
        calc.nitrogenRule = struct.nitrogenRule

        for p in calc.getInitedElements():
            del calc[p]

        disabled = set(chain(calc.getElements(), calc.getIsotopes()))

        for p in struct.params:
            calc[p.element] = p.get_params()
        for e in chain(struct.elements.split(','), struct.isotopes.split(',')):
            if not e:
                continue
            calc.setEI(e, True)
            if e in disabled:
                disabled.remove(e)
        for e in disabled:
            if not e:
                continue
            calc.setEI(e, False)
        return calc


class ForceElementNumItem(BaseRowItem):
    item_name = "force calc element num"
    ei_name: AsciiLimit[10]
    max_num: int


class ForceCalcStructure(BaseStructure):
    h5_type = "force calc"
    rtol: float
    ei_list: Row[ForceElementNumItem]


class ForceCalcHandler(StructureTypeHandler):
    def write_to_h5(self, h5group: Group, key: str, value: ForceCalc):
        ei_list = [ForceElementNumItem(ei_name=e, max_num=value[e])
                   for e in value.getEIList()]
        struct = ForceCalcStructure(value.rtol, ei_list)
        handler: StructureTypeHandler = get_handler(BaseStructure)
        handler.write_to_h5(h5group, key, struct)

    def read_from_h5(self, h5group: Group, key: str):
        handler: StructureTypeHandler = get_handler(BaseStructure)
        struct: ForceCalcStructure = handler.read_from_h5(h5group, key)
        calc = ForceCalc()
        for ei in calc.getEIList():
            calc[ei] = 0
        calc.rtol = struct.rtol
        for ei in struct.ei_list:
            calc[ei.ei_name] = ei.max_num
        return calc


register_handler(Formula, FormulaHandler)
register_handler(RestrictedCalc, RestrictedCalcHandler)
register_handler(ForceCalc, ForceCalcHandler)
