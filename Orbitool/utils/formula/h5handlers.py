from functools import lru_cache
from itertools import chain
from typing import Any, List, Union

import numpy as np
from h5py import Group
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from Orbitool.base.extra_type_handlers.simple_handlers import StrTypeHandler
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


class FormulaType(Formula):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def validate(value):
            if isinstance(value, Formula):
                return value
            if isinstance(value, (str, dict)):
                return Formula(value)
            assert False

        return core_schema.no_info_before_validator_function(
            validate, handler(Any))


class FormulaTypeHandler(StrTypeHandler):
    target_type = FormulaType

    def convert_from_attr(self, value):
        if isinstance(value, bytes):
            value = value.decode()
        return Formula(value)

    def convert_to_column(self, value: List[Formula]) -> np.ndarray:
        return np.array(list(map(str, value)), self.h5_dtype)

    def convert_from_column(self, value: np.ndarray) -> List[Formula]:
        return list(map(Formula, value.tolist()))


register_handler(Formula, FormulaHandler)
