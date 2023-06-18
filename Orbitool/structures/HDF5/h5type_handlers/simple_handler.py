from datetime import date, datetime

from h5py import string_dtype
import numpy as np

from .base import *


class AttrHandler(StructureTypeHandler):
    def write_to_h5(self, h5group: Group, key: str, value):
        h5group.attrs[key] = value

    def read_from_h5(self, h5group: Group, key: str):
        return h5group.attrs[key]


class IntHandler(AttrHandler, RowDTypeHandler):
    def validate(self, value):
        return int(value)

    def dtype(self):
        return np.int64


class FloatHandler(AttrHandler, RowDTypeHandler):
    def validate(self, value):
        return float(value)

    def dtype(self):
        return np.dtype(np.float64)


class BoolHandler(AttrHandler, RowDTypeHandler):
    def validate(self, value):
        return bool(value)

    def dtype(self):
        return np.dtype(bool)


class StrHandler(AttrHandler, RowDTypeHandler):
    def validate(self, value):
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode()
        return str(value)

    def dtype(self):
        return string_dtype('utf-8')

    def convert_from_h5(self, value):
        if isinstance(value, bytes):
            return value.decode()
        return value


class DatetimeConverter(AttrHandler, RowDTypeHandler):
    def validate(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)

    def write_to_h5(self, h5group: Group, key: str, value):
        h5group.attrs[key] = str(value)

    def read_from_h5(self, h5group: Group, key: str):
        return datetime.fromisoformat(h5group.attrs[key])

    def dtype(self):
        return np.dtype(np.int64)

    def convert_to_h5(self, value):
        if value is None:
            return 0
        return np.datetime64(value, 's').astype(np.int64)

    def convert_from_h5(self, value) -> datetime | None:
        if value == 0:
            return None
        return value.astype('M8[s]').astype(datetime)


class DateConverter(DatetimeConverter):
    def validate(self, value):
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()

    def read_from_h5(self, h5group: Group, key: str):
        return date.fromisoformat(h5group.attrs[key])

    def convert_from_h5(self, value):
        ret = super().convert_from_h5(value)
        return ret.date() if ret is not None else None


class AsciiLimit(StrHandler, RowDTypeHandler, str):
    def __init__(self, args) -> None:
        super().__init__(args=args)
        self.length = self.args[0]

    def __call__(self, value):
        return str(value)

    def dtype(self):
        return np.dtype(f"S{self.length}")
