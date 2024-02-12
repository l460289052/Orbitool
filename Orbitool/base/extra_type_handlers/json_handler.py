

import json
from types import GenericAlias
from typing import Any, List, Type, TypeVar
import numpy as np

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema
from pydantic_core import core_schema

from Orbitool.base.structure import AttrTypeHandler
from .column_handler import StrTypeHandler as StrColumnCellTypeHandler

T = TypeVar("T")


class JSONObject:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def validate(value):
            return value
        return core_schema.no_info_before_validator_function(validate, handler(Any))


class JSONObjectTypeHandler(AttrTypeHandler):
    target_type = JSONObject

    def convert_to_attr(self, value):
        return json.dumps(value, ensure_ascii=False)

    def convert_from_attr(self, value: str):
        return json.loads(value)


class JSONObjectColumnCellTypeHandler(StrColumnCellTypeHandler):
    column_target = JSONObject

    def convert_to_npcolumn(self, value: List[JSONObject]) -> np.ndarray:
        return super().convert_to_npcolumn([json.dumps(v, ensure_ascii=False) for v in value])

    def convert_from_npcolumn(self, value: np.ndarray) -> List[JSONObject]:
        return list(map(json.loads, super().convert_from_npcolumn(value)))
