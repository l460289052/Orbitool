from functools import lru_cache
from typing import Any, Generic, Iterable, List, Optional, Tuple, Type, TypeVar, Union
from h5py import Group as H5Group, Dataset as H5Dataset  # , string_dtype
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
    "S", "U"  # bytes, unicode
}

OTHERS = {
    "?", "M", "m"  # bool, datetime, timedelta
}

SUPPORTED = INTS.union(FLOATS, STRS, OTHERS)

# strdtype = string_dtype(encoding='utf-8')


def support(dtype: np.dtype):
    return dtype.char in SUPPORTED  # or dtype == strdtype


int64 = np.dtype('int64')


class Converter:
    def __init__(self, dtype: np.dtype) -> None:
        self.dtype = dtype
        self.h5_dtype = dtype

    def convert_to_h5(self, value: np.ndarray):
        return value

    def convert_from_h5(self, value: np.ndarray):
        return value


class TimesConverter(Converter):
    def __init__(self, dtype: np.dtype) -> None:
        self.dtype = dtype
        self.h5_dtype = int64

    def convert_to_h5(self, value: np.ndarray):
        return value.astype(self.h5_dtype)

    def convert_from_h5(self, value: np.ndarray):
        return value.astype(self.dtype)


# class StringConverter(Converter):
#     """
#     h5py has a bug
#     ```python
#         strd = h5py.string_dtype(encoding='utf8')
#         d = f.create_dataset('s', shape=10, dtype=
#             np.dtype(
#                 [("a", "int64"),
#                 ("b", strd)]))
#         assert d["b"].dtype == strd

#         # TypeError: Cannot change data-type for object array.
#         d["b"] = np.array(['123']*10, dtype=strd)

#         # Success
#         d["b"] = np.array(['123']*10, dtype=[("b", strd)])
#     ```

#     """

#     def __init__(self, dtype: np.dtype, title: Optional[str]) -> None:
#         self.dtype = dtype
#         self.h5_dtype = self.dtype
#         if title is not None:
#             self.true_h5_dtype = np.dtype([(title, dtype)])
#         self.title = title

#     def convert_to_h5(self, value: np.ndarray):
#         if self.title is not None:
#             return value.astype(self.true_h5_dtype)
#         else:
#             return value

#     def convert_from_h5(self, value: np.ndarray):
#         """
#         stupid h5py
#         ```python
#             sd = string_dtype(encoding='utf-8')
#             a = np.array(['123']*10, dtype=sd)
#             assert type(a[0]) == str

#             d = f.create_dataset('s', shape=10, dtype=sd)
#             d[:] = a

#             # Error! type of d[0] is bytes!
#             assert type(d[0]) == str
#         ```
#         """
#         if len(value) and isinstance(value[0], bytes):
#             value = value.astype(str)
#         return value

class StringConverter(Converter):
    def __init__(self, dtype: np.dtype) -> None:
        self.dtype = dtype
        self.h5_dtype = np.dtype("S")

    def convert_to_h5(self, value: np.ndarray):
        """
            https://github.com/numpy/numpy/issues/13156
        """
        if len(value):
            return np.char.encode(value, encoding='utf-8')
        else:
            return np.empty_like(value, dtype=self.h5_dtype)

    def convert_from_h5(self, value: np.ndarray):
        if len(value):
            if value.dtype.char != 'S':  # reading old files
                value = value.astype("S")
            return np.char.decode(value, encoding='utf-8')
        else:
            return np.empty_like(value, dtype=self.dtype)


@lru_cache(None)
def get_converter(dtype: np.dtype):
    match dtype.char:
        case 'm' | 'M':
            return TimesConverter(dtype)
        case 'U':
            return StringConverter(dtype)
    return Converter(dtype)


class HomogeneousNdArrayHelper:
    def __init__(self, dtype: np.dtype) -> None:
        assert support(dtype)
        self.dtype = dtype
        self.converter = get_converter(dtype)
        self.is_s = self.converter.h5_dtype.char == "S"

    def write(self, h5g: H5Group, key: str, value: np.ndarray):
        value = self.converter.convert_to_h5(value)
        if self.is_s:
            return h5g.create_dataset(key, data=value, **H5_DT_ARGS)
        return h5g.create_dataset(key, data=value, dtype=self.converter.h5_dtype, **H5_DT_ARGS)

    def read(self, dataset: H5Dataset) -> np.ndarray:
        return self.converter.convert_from_h5(dataset[()])


class HeteroGeneousNdArrayHelper:
    def __init__(self, dtype_list: List[Union[Tuple[str, np.dtype], Tuple[str, np.dtype, Union[int, Tuple[int]]]]]) -> None:
        converters: List[Converter] = []
        h5_dtype = []
        s_type = []
        has_s = False
        for dtype in dtype_list:
            typ = dtype[1]
            assert support(typ)
            converter = get_converter(typ)
            converters.append(converter)

            h5_dtype.append((dtype[0], converter.h5_dtype, *dtype[2:]))
            if converter.h5_dtype.char == "S":
                s_type.append(True)
                has_s = True
            else:
                s_type.append(False)

        self.dtype_list = dtype_list
        self.converters = converters
        self.h5_dtype_list = h5_dtype
        self.h5_dtype = np.dtype(h5_dtype)
        self.s_type = s_type
        self.has_s = has_s

    def columns_write(self, h5g: H5Group, key: str, length: int, columns: Iterable[np.ndarray]):
        if self.has_s:
            h5_dtype_list = self.h5_dtype_list
            columns = [cvt.convert_to_h5(column) for cvt, column in zip(self.converters, columns, strict=True)]
            if columns:
                col_len = np.array([len(col) for col in columns]) 
                assert (col_len == length).all(), f"Error length: {h5g.name=} {key=} {length=} {col_len=}"
            h5_dtype = [(dtype[0], col.dtype if s else dtype[1], *dtype[2:])
                        for dtype, s, col in zip(h5_dtype_list, self.s_type, columns, strict=True)]
            ds = h5g.create_dataset(key, length, h5_dtype, **H5_DT_ARGS)
            for dtype, column in zip(self.h5_dtype_list, columns, strict=True):
                ds[dtype[0]] = column
        else:
            ds = h5g.create_dataset(key, length, self.h5_dtype, **H5_DT_ARGS)
            for dtype, cvt, column in zip(self.h5_dtype_list, self.converters, columns, strict=True):
                assert len(column) == length, f"Error length: {h5g.name} {key=} {length=} {dtype[0]=} {len(column)=}"
                ds[dtype[0]] = cvt.convert_to_h5(column)
        return ds

    def columns_read(self, dataset: H5Dataset):
        names = set(dataset.dtype.names)
        for dtype, cvt in zip(self.h5_dtype_list, self.converters, strict=True):
            yield cvt.convert_from_h5(dataset[dtype[0]]) if dtype[0] in names else None
