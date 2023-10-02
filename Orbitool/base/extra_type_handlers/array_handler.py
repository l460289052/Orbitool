from __future__ import annotations
from array import array
from types import GenericAlias
from typing import Any, Iterable, List, Literal, Tuple, Type, TypeVar, overload, Union, get_args
from h5py import Dataset as H5Dataset, Group as H5Group
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

import numpy as np

from .base import *
from .np_helper import HomogeneousArrayHelper

array_dtypes = {
    "b": np.int8,
    "B": np.uint8,
    "h": np.int16,
    "H": np.uint16,
    "i": np.int32,
    "I": np.uint32,
    "l": np.int32,
    "L": np.uint32,
    "q": np.int64,
    "Q": np.uint64,
    "f": np.float32,
    "d": np.float64
}

str_dtypes = {
    "int8": "b",
    "uint8": "B",
    "int16": "h",
    "uint16": "H",
    "int32": "i",
    "uint32": "I",
    "int64": "q",
    "uint64": "Q",
    "float32": "f",
    "float64": "d"
}

py_dtypes = {
    int: "i",
    float: "d"
}

dtype_convert = str_dtypes | py_dtypes

_IntTypeCode = Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q"]
_FloatTypeCode = Literal["f", "d"]
_UnicodeTypeCode = Literal["u"]
_TypeCode = _IntTypeCode | _FloatTypeCode | _UnicodeTypeCode


class Array(array):
    def __class_getitem__(cls, args: _TypeCode):
        args = dtype_convert.get(args, args)
        return GenericAlias(Array, args)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        args = get_args(source_type)
        if not args:
            raise AnnotationError("Please provide args for Array")
        type_code = args[0]

        def validate(value):
            if value is None:
                return None
            if isinstance(value, array) and value.typecode == type_code:
                return value
            if isinstance(value, Iterable):
                return array(type_code, value)
            assert False
        return core_schema.no_info_before_validator_function(validate, handler(Any))


class ArrayTypeHandler(DatasetTypeHandler, RowTypeHandler):
    target_type = Array

    def __post_init__(self):
        self.type_code: _TypeCode = self.args[0]
        self.h5_dtype = np.dtype(self.type_code)
        self.helper = HomogeneousArrayHelper(self.h5_dtype)

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value):
        self.helper.write(h5g, key, value)

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        return array(self.type_code, self.helper.read(dataset))

    def convert_to_column(self, value: array) -> np.ndarray:
        return np.array(value, dtype=self.h5_dtype)

    def convert_from_column(self, value: np.ndarray) -> array:
        return array(self.type_code, value)
