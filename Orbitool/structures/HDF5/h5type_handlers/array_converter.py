import array
from typing import overload, Union, Type, TypeVar

import numpy as np
from h5py import Group

from .base import TypeHandler, register_handler

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

T = TypeVar("T", Type[int], Type[float])


class Array(TypeHandler, array.array):
    @overload
    def __class_getitem__(
        cls, typecode: str): ...

    @overload
    def __class_getitem__(cls, type: T) -> Type[array.array]: ...

    def __class_getitem__(cls, args):
        return super().__class_getitem__(py_dtypes.get(args, args))

    def __call__(self, value):
        return array.array(self.args[0], value)

    @classmethod
    def write_to_h5(cls, args: tuple, h5group: Group, key: str, value):
        h5group.create_dataset(
            key, data=value, dtype=array_dtypes[args[0]], compression="gzip", compression_opts=1)

    @classmethod
    def read_from_h5(cls, args: tuple, h5group: Group, key: str):
        h5obj = h5group[key]
        return array.array(args[0], h5obj[()])
