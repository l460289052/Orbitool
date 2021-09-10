import array
from datetime import date, datetime

from h5py import Group
import numpy as np

from .converters import BaseSingleConverter, AttrConverter, register_converter


class DatetimeConverter(AttrConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: datetime):
        h5group.attrs[key] = value.isoformat()

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return datetime.fromisoformat(h5group.attrs[key])


class DateConverter(AttrConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: date):
        h5group.attrs[key] = value.isoformat()

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return date.fromisoformat(h5group.attrs[key])


class NumpyConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value):
        if key in h5group:
            del h5group[key]
        h5group.create_dataset(
            key, data=value, compression="gzip", compression_opts=1)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return h5group[key][()]


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


class ArrayConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: array.ArrayType):
        if key in h5group:
            del h5group[key]
        h5group.create_dataset(
            key, data=value, dtype=array_dtypes[value.typecode], compression="gzip", compression_opts=1)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        h5obj = h5group[key]
        return array.array(str_dtypes[str(h5obj.dtype)], h5obj[()])


register_converter(bool, AttrConverter)
register_converter(int, AttrConverter)
register_converter(str, AttrConverter)
register_converter(float, AttrConverter)
register_converter(date, DateConverter)
register_converter(datetime, DatetimeConverter)
register_converter(np.ndarray, NumpyConverter)
register_converter(array.ArrayType, ArrayConverter)
