from types import EllipsisType, GenericAlias
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Sequence, Tuple, Union, get_args, overload

import numpy as np
from h5py import Dataset as H5Dataset, Group as H5Group
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from .base import *
from .np_helper import HomogeneousArrayHelper, support, get_converter


class ParsedArgs(NamedTuple):
    dtype: Union[np.dtype, EllipsisType]
    shape: Union[int, Tuple[int], EllipsisType]
    index: Union[int, Literal[-1]]


def parse_args(args):
    match len(args):
        case 0:
            dtype = shape = ...
        case 1:
            dtype = args[0]
            shape = ...
        case 2:
            dtype, shape = args
        case _:
            raise AnnotationError(
                f"Ndarray args error, args should be [dtype, shape]: {args}")
    if dtype is not ...:
        dtype = np.dtype(dtype)
        if not support(dtype):
            raise AnnotationError(
                f"Ndarray args error, type is not supported: {args}")

    ind = -1
    if shape is not ...:
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
            if value is None:
                return None
            if not isinstance(value, np.ndarray):
                if dtype is not ...:
                    value = np.array(value, dtype)
                else:
                    value = np.array(value)
            if dtype is not ... and value.dtype != dtype:
                value = value.astype(dtype)
            if shape is not ...:
                if ind > -1:
                    assert shape[:ind] == value.shape[:ind]
                    assert shape[ind + 1:] == value.shape[ind + 1:]
                else:
                    assert shape == value.shape
            return value
        return core_schema.no_info_before_validator_function(validate, handler(Any))


class NdArrayTypeHandler(DatasetTypeHandler):
    target_type = NdArray

    def __post_init__(self):
        self.dtype, self.shape, self.index = parse_args(self.args)
        self.helper = HomogeneousArrayHelper(self.dtype)

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: np.ndarray):
        self.helper.write(h5g, key, value)

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        return self.helper.read(dataset)


class AttrNdArray(NdArray):
    pass


class AttrNdArrayTypeHandler(AttrTypeHandler):
    target_type = AttrNdArray

    def __post_init__(self):
        self.dtype, self.shape, self.index = parse_args(self.args)
        self.converter = get_converter(self.dtype)

    def convert_to_attr(self, value: np.ndarray):
        return self.converter.convert_to_h5(value)

    def convert_from_attr(self, value: np.ndarray):
        return self.converter.convert_from_h5(value)
