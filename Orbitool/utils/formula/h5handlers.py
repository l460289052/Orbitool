from functools import lru_cache
from itertools import chain
from typing import List

import numpy as np
from h5py import Group

from ...structures import (BaseRowItem, BaseStructure, RowDTypeHandler,
                           StructureTypeHandler, get_handler, register_handler)
from ...structures.HDF5 import AsciiLimit, Row
from ...structures.HDF5.h5type_handlers import AttrHandler, StrHandler
from ._formula import Formula


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


register_handler(Formula, FormulaHandler)
