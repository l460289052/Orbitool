from typing import Any, Iterable, List, Union

import numpy as np
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from Orbitool.base.extra_type_handlers.simple_handlers import StrTypeHandler
from ._formula import Formula


def validate_formula(value):
    if isinstance(value, Formula):
        return value
    if isinstance(value, (str, dict)):
        return Formula(value)
    assert False


class FormulaType(Formula):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_before_validator_function(
            validate_formula, handler(Any))


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


def validate_formula_list(value):
    if isinstance(value, str):
        value = [v.strip() for v in value.split(', ')]
    if isinstance(value, Iterable):
        return list(map(validate_formula, value))
    assert False


class FormulaList(list):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_before_validator_function(
            validate_formula_list, handler(Any))


class FormulaListTypeHandler(StrTypeHandler):
    target_type = FormulaList

    def convert_to_attr(self, value: List[Formula]):
        return ', '.join(map(str, value))

    def convert_from_attr(self, value):
        return validate_formula_list(value)

    def convert_to_column(self, value: List[List[Formula]]) -> np.ndarray:
        return np.array(list(map(self.convert_to_attr, value)), self.h5_dtype)
    
    def convert_from_column(self, value: np.ndarray) -> list:
        return list(map(validate_formula_list, value.tolist()))
