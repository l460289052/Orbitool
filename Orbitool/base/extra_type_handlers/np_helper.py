from functools import lru_cache
from typing import Any, Generic, Iterable, List, Tuple, Type, TypeVar
from h5py import Group as H5Group, Dataset as H5Dataset, string_dtype
import numpy as np
from .base import *

H5_DT_ARGS = {
    "compression": "gzip",
    "compression_opts": 1
}

INTS = {
    "b", "B", "h", "H", "i", "I", "l", "L", "q", "Q",  # byte, short, int32, int64
}

FLOATS = {
    "e", "f", "d", "g"  # f16, f32, f64, f128
}

STRS = {
    "S", string_dtype(encoding='utf-8')  # bytes, unicode
}

OTHERS = {
    "?"  # bool
}

SUPPORTED = INTS.union(FLOATS, STRS, OTHERS)


def support(dtype: np.dtype):
    return dtype.char in SUPPORTED


int64 = np.dtype('int64')


class Converter:
    def __init__(self, dtype: np.dtype) -> None:
        self.dtype = dtype
        self.h5_dtype = dtype

    def convert_to_h5(self, value: np.ndarray):
        return value, self.dtype

    def convert_from_h5(self, value: np.ndarray):
        return value


class TimesConverter(Converter):
    def __init__(self, dtype: np.dtype) -> None:
        self.dtype = dtype
        self.h5_dtype = int64

    def convert_to_h5(self, value: np.ndarray):
        return value.astype(int64), int64

    def convert_from_h5(self, value: np.ndarray):
        return value.astype(self.dtype)


@lru_cache(None)
def get_converter(dtype: np.dtype):
    if dtype.char.lower() == 'm':
        return TimesConverter(dtype)
    return Converter(dtype)


class HomogeneousArrayHelper:
    def __init__(self, dtype: np.dtype) -> None:
        assert support(dtype)
        self.dtype = dtype
        self.converter = get_converter(dtype)

    def write(self, h5g: H5Group, key: str, value: np.ndarray):
        value, dtype = self.converter.convert_to_h5(value)
        return h5g.create_dataset(key, data=value, dtype=dtype, **H5_DT_ARGS)

    def read(self, dataset: H5Dataset) -> np.ndarray:
        return self.converter.convert_from_h5(dataset[()])


class HeteroGeneousArrayHelper:
    def __init__(self, titles: List[str], dtypes: List[np.dtype]) -> None:
        assert all(map(support, dtypes))
        self.titles = titles
        self.dtypes = dtypes
        self.converters = list(map(get_converter, dtypes))
        self.h5_dtype = np.dtype(
            [(title, cvt.h5_dtype) for title, cvt in zip(titles, self.converters)])

    def columns_write(self, h5g: H5Group, key: str, length: int, columns: Iterable[np.ndarray]):
        ds = h5g.create_dataset(key, length, self.h5_dtype, **H5_DT_ARGS)
        for title, cvt, column in zip(self.titles, self.converters, columns):
            ds[title] = cvt.convert_to_h5(column)
        return ds

    def columns_read(self, dataset: H5Dataset):
        for title, cvt in zip(self.titles, self.converters):
            yield cvt.convert_from_h5(dataset[title])


T = TypeVar("T")


class PyListHelper(Generic[T]):
    def __init__(self, typ: Type[T]) -> None:
        self.handler: RowTypeHandler = get_handler(typ)
        assert isinstance(self.handler, RowTypeHandler)
        self.dtype = self.handler.h5_dtype
        self.array_helper = HomogeneousArrayHelper(self.dtype)

    def write_to_h5(self, h5g: H5Group, key: str, value: List[T]):
        return self.array_helper.write(h5g, key, self.handler.convert_to_column(value))

    def read_from_h5(self, dataset: H5Dataset):
        return self.handler.convert_from_column(self.array_helper.read(dataset))


class PyColumnsHelper:
    def __init__(self, titles: Tuple[str], types: tuple) -> None:
        handlers: List[RowTypeHandler] = []
        dtypes: List[np.dtype] = []
        for typ in types:
            handler = get_handler(typ)
            assert isinstance(handler, RowTypeHandler)
            handlers.append(handler)
            dtypes.append(handler.h5_dtype)
        self.titles = titles
        self.handlers = handlers
        self.dtypes = dtypes
        self.array_helper = HeteroGeneousArrayHelper(titles, dtypes)

    def write_columns_to_h5(self, h5g: H5Group, key: str, length: int, columns: Iterable[list]):
        h5_columns = []
        for handler, column in zip(self.handlers, columns):
            h5_columns.append(handler.convert_to_column(column))
        return self.array_helper.columns_write(h5g, key, self.titles, length, h5_columns)

    def read_columns_from_h5(self, dataset: H5Dataset):
        columns_iter = HeteroGeneousArrayHelper.columns_read(
            dataset, self.titles, self.dtypes)
        columns = []
        for handler, column in zip(self.handlers, columns_iter):
            columns.append(handler.convert_from_column(column))
        return columns
