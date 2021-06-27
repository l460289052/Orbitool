from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Tuple, Type, TypeVar

import numpy as np
from h5py import Group, string_dtype
from pydantic.fields import ModelField

from ..base import BaseTableItem, items


@lru_cache(None)
def get_dtype(item_type: BaseTableItem) -> Tuple[list, Dict[str, Type[Dtype]]]:
    dtypes = []
    converter = {}
    for key, field in item_type.__fields__.items():
        if key != "item_name":
            dtype = type_dtype.get(field.outer_type_, field.outer_type_)

            if not issubclass(dtype if isinstance(dtype, type) else type(dtype), Dtype):
                raise TypeError(
                    f'{items.get_name(item_type)} member "{key}" type "{dtype}" should be registered or as a subclass of Dtype')
            if not hasattr(dtype, "dtype"):
                raise TypeError(
                    f"Maybe you should use {dtype}[some argument] instead of {dtype}")
            dtypes.append((key, dtype.dtype))
            converter[key] = dtype
    return dtypes, converter


T = TypeVar('T')


class TableConverter:
    @staticmethod
    def write_to_h5(h5group: Group, key: str, item_type: Type[T], values: List[T]):
        dtype, converter = get_dtype(item_type)
        dataset = h5group.create_dataset(
            key, (len(values),), dtype, compression="gzip", compression_opts=1)
        rows = [tuple(conv.convert_to_h5(getattr(value, k))
                      for k, conv in converter.items()) for value in values]

        dataset[:] = rows
        dataset.attrs["item_name"] = item_type.__fields__["item_name"].default

    @staticmethod
    def read_from_h5(h5group: Group, key: str, item_type: Type[T]) -> List[T]:
        dtype, converter = get_dtype(item_type)
        dataset = h5group[key]

        rows = dataset[:]
        return [item_type(**{key: conv.convert_from_h5(value) for value, (key, conv) in zip(row, converter.items())}) for row in rows]


class Dtype:
    dtype = None

    @staticmethod
    def convert_to_h5(value):
        return value

    @staticmethod
    def convert_from_h5(value):
        return value


class IntDtype(Dtype):
    dtype = np.dtype(np.int64)


class FloatDtype(Dtype):
    dtype = np.dtype(np.float64)


class BoolDtype(Dtype):
    dtype = np.dtype(np.bool)


class StrDtype(Dtype):
    dtype = string_dtype('utf-8')


class DatetimeDtype(IntDtype):
    @staticmethod
    def convert_to_h5(value):
        return np.datetime64(value, 's').astype(np.int64)

    @staticmethod
    def convert_from_h5(value):
        return value.astype('M8[s]').astype(datetime)


type_dtype: Dict[Type, Type[Dtype]] = {
    int: IntDtype,
    float: FloatDtype,
    bool: BoolDtype,
    str: StrDtype,
    datetime: DatetimeDtype
}


class BaseDatatableType(Dtype):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v): ...


class Int32(int, BaseDatatableType):
    dtype = np.dtype(np.int32)

    @classmethod
    def validate(cls, v):
        return int(v)


class AsciiLimit(BaseDatatableType):
    def __init__(self, length) -> None:
        self.length = length
        self.dtype = np.dtype(f"S{length}")

    def __class_getitem__(cls, length):
        return AsciiLimit(length)

    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            return v.decode()
        return str(v)


def register_datatable_converter(typ, converter: Type[Dtype]):
    type_dtype[typ] = converter
