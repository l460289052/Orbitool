from functools import reduce
import operator
from types import EllipsisType, GenericAlias
from typing import (TYPE_CHECKING, Any, List, Literal, NamedTuple, Sequence, Tuple,
                    Union, get_args, overload)

import numpy as np
from h5py import Dataset as H5Dataset
from h5py import Group as H5Group
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from .base import *
from .column_handler import ColumnCellTypeHandler, ColumnHandler
from .np_helper import HomogeneousNdArrayHelper, get_converter, support


class ParsedArgs(NamedTuple):
    dtype: Union[np.dtype, EllipsisType]
    shape: Union[Tuple[int], EllipsisType]
    index: Union[int, Literal[-1]]


def parse_args(args):
    match len(args):
        case 0:
            dtype = shape = None
        case 1:
            dtype = args[0]
            shape = None
        case 2:
            dtype, shape = args
        case _:
            raise AnnotationError(
                f"Ndarray args error, args should be [dtype, shape]: {args}")
    if dtype is not None:
        dtype = np.dtype(dtype)
        if not support(dtype):
            raise AnnotationError(
                f"Ndarray args error, type is not supported: {args}")

    ind = -1
    if shape is not None:
        if not isinstance(shape, tuple):
            shape = (shape,)
        if sum(s == -1 for s in shape) > 1:
            raise AnnotationError(f"Ndarray args error, too many -1: {args}")
        for i, s in enumerate(shape):
            if s == -1:
                ind = i
    return ParsedArgs(dtype, shape, ind)


class NdArray(np.ndarray):
    """
    NdArray[int]
    NdArray[int, -1]
    NdArray[int, 100]
    NdArray[int, ...]
    NdArray[..., (2, 3, -1)]
    NdArray[int, (2, 3, -1)]
    """
    @overload
    def __class_getitem__(cls, type: type): ...
    @overload
    def __class_getitem__(cls, type_shape: Tuple[type, int]): ...
    @overload
    def __class_getitem__(cls, type_shape: Tuple[type, Tuple[int]]): ...

    def __class_getitem__(cls, args):
        return GenericAlias(cls, args)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        dtype, shape, ind = parse_args(get_args(source_type))

        def validate(value):
            # because we need to store them to h5, and when load back, the shape is (0,)
            assert value is not None, f"cannot be None."
            if not isinstance(value, np.ndarray):
                if dtype is not None:
                    value = np.array(value, dtype)
                else:
                    value = np.array(value)
            if dtype is not None and value.dtype != dtype:
                value = value.astype(dtype)
            if shape is not None:
                if ind > -1:
                    assert shape[:ind] == value.shape[:ind], f"wrong shape, want {shape}, given {value.shape}"
                    assert shape[ind + 1:] == value.shape[ind + 1:], f"wrong shape, want {shape}, given {value.shape}"
                else:
                    assert shape == value.shape, f"wrong shape, want {shape}, given {value.shape}"
            return value
        return core_schema.no_info_before_validator_function(validate, handler(Any))

# dataset -> ndarray as a column -> ColumnHandler, 现在只考虑一维的场景
# list/dict -> ndarray in row as a column -> ColumnCellTypeHandler, 现在需要考虑多维场景

class NdArrayTypeHandler(ColumnHandler):
    target_type = NdArray

    def __post_init__(self):
        self.dtype, self.shape, self.index = parse_args(self.args)
        self.helper = HomogeneousNdArrayHelper(self.dtype)

    def get_cell_shape(self):
        shape = self.shape
        assert self.index == 0, "shape must be specific for column"
        if shape is None or len(shape) == 1:
            return None
        """
        stupid h5py don't support set value by name when multidimension dtype
        ```python
            d = f.create_dataset('d', shape=10,dtype=[('a', int), ('b', float, (2,3))])
            # ValueError: When changing to a larger dtype, its size must be a divisor of the total size in bytes of the last axis of the array.
            d['b'] = d['b'] 

            # single dimension
            e = f.create_dataset('e', shape=10,dtype=[('a', int), ('b', float, 6)])
            # works
            e['b'] = e['b'] 
            e['b'] == np.empty((10, 6), dtype=float)
        ```
        """
        return (reduce(operator.mul, shape[1:]),)

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: np.ndarray):
        return self.helper.write(h5g, key, value)

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        return self.helper.read(dataset)

    def convert_to_ndarray(self, value: np.ndarray):
        shape = self.shape
        if shape is None or len(shape) == 1:
            assert len(value.shape) == 1
            return value
        return value.reshape(value.shape[0], -1)

    def convert_from_ndarray(self, value: np.ndarray):
        shape = self.shape
        if shape is None or len(shape) == 1:
            return value
        return value.reshape(shape)


class NdArrayCellTypeHandler(ColumnCellTypeHandler[NdArray]):
    column_target = NdArray

    def __post_init__(self):
        assert len(self.args) == 2, "Must provide shape for column array"
        self.dtype, shape, ind = parse_args(self.args)
        self.shape = (reduce(operator.mul, shape), )
        assert ind < 0, "shape must be specific"

    def convert_to_npcolumn(self, value: List[NdArray]) -> np.ndarray:
        return np.stack(value, 0, dtype=self.dtype).reshape(len(value), -1)

    def convert_from_npcolumn(self, value: np.ndarray) -> List[NdArray]:
        return list(value.reshape(-1, *self.args[1]))


class AttrNdArray(NdArray):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        dtype, shape, ind = parse_args(get_args(source_type))

        def validate(value):
            if value is None:
                return None  # for attr nd, it could be none
            if not isinstance(value, np.ndarray):
                if dtype is not None:
                    value = np.array(value, dtype)
                else:
                    value = np.array(value)
            if dtype is not None and value.dtype != dtype:
                value = value.astype(dtype)
            if shape is not None:
                if ind > -1:
                    assert shape[:ind] == value.shape[:ind], f"wrong shape, want {shape}, given {value.shape}"
                    assert shape[ind + 1:] == value.shape[ind + 1:], f"wrong shape, want {shape}, given {value.shape}"
                else:
                    assert shape == value.shape, f"wrong shape, want {shape}, given {value.shape}"
            return value
        return core_schema.no_info_before_validator_function(validate, handler(Any))


class AttrNdArrayTypeHandler(AttrTypeHandler):
    target_type = AttrNdArray

    def __post_init__(self):
        self.dtype, self.shape, self.index = parse_args(self.args)
        self.converter = get_converter(self.dtype)

    def convert_to_attr(self, value: np.ndarray):
        return self.converter.convert_to_h5(value)

    def convert_from_attr(self, value: np.ndarray):
        return self.converter.convert_from_h5(value)
