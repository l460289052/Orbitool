from functools import lru_cache

import numpy as np
from typing import List
from h5py import Group, string_dtype
from itertools import chain

from ..utils.formula import Formula, ForceCalc, RestrictedCalc
from . import HDF5
from .HDF5 import BaseSingleConverter, TableConverter, StructureConverter, h5datatable
from .base import BaseStructure, BaseTableItem


class FormulaConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: Formula):
        h5group.attrs[key] = str(value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return Formula(h5group.attrs[key])


class FormulaDatatableConverter(TableConverter):
    dtype = string_dtype()

    @staticmethod
    def convert_to_h5(value):
        return str(value)

    @staticmethod
    def convert_from_h5(value):
        return Formula(value)


class RestrictedCalcElementNumItem(BaseTableItem):
    item_name = "restriced cac formula num"

    element: h5datatable.AsciiLimit[10]
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
    charge: int
    params: List[RestrictedCalcElementNumItem]
    elements: str
    isotopes: str


class RestrictedCalcConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: RestrictedCalc):
        parameters = [RestrictedCalcElementNumItem(element=e, **value[e])
                      for e in value.getInitedElements()]
        elements = ','.join(value.getElements())
        isotopes = ','.join(value.getIsotopes())
        struct = RestrictedCalcStructure(
            rtol=value.rtol, charge=value.charge, params=parameters, elements=elements, isotopes=isotopes)
        StructureConverter.write_to_h5(h5group, key, struct)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        struct: RestrictedCalcStructure = StructureConverter.read_from_h5(
            h5group, key)
        calc = RestrictedCalc()

        calc.rtol = struct.rtol
        calc.charge = struct.charge
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


class ForceElementNumItem(BaseTableItem):
    item_name = "force calc element num"
    ei_name: h5datatable.AsciiLimit[10]
    max_num: int


class ForceCalcStructure(BaseStructure):
    h5_type = "force calc"
    rtol: float
    charge: int
    ei_list: List[ForceElementNumItem]


class ForceCalcConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: ForceCalc):
        ei_list = [ForceElementNumItem(ei_name=e, max_num=value[e])
                   for e in value.getEIList()]
        struct = ForceCalcStructure(
            rtol=value.rtol, charge=value.charge, ei_list=ei_list)
        StructureConverter.write_to_h5(h5group, key, struct)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        struct: ForceCalcStructure = StructureConverter.read_from_h5(
            h5group, key)
        calc = ForceCalc()
        for ei in calc.getEIList():
            calc[ei] = 0
        calc.rtol = struct.rtol
        calc.charge = struct.charge
        for ei in struct.ei_list:
            calc[ei.ei_name] = ei.max_num
        return calc
