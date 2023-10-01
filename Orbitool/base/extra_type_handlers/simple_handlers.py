import abc
from datetime import date, datetime, timedelta
from typing import Any, List, final

from h5py import string_dtype
import numpy as np

from .base import *


class IntTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = int
    h5_dtype = np.dtype("int64")

    def convert_to_attr(self, value):
        return int(value)

    def convert_from_attr(self, value):
        return int(value)


class FloatTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = float
    h5_dtype = np.dtype("float64")

    def convert_to_attr(self, value):
        return float(value)

    def convert_from_attr(self, value):
        return float(value)


class BoolTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = bool
    h5_dtype = np.dtype("bool")

    def convert_to_attr(self, value):
        return bool(value)

    def convert_from_attr(self, value):
        return bool(value)


class StrTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = str
    h5_dtype = string_dtype(encoding="utf-8")

    def convert_to_attr(self, value):
        return str(value)

    def convert_from_attr(self, value):
        if isinstance(value, bytes):
            return value.decode()
        return value


class DatetimeTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = datetime
    h5_dtype = np.dtype("datetime64[us]")

    def convert_to_attr(self, value: datetime):
        return str(value)

    def convert_from_attr(self, value: str):
        return datetime.fromisoformat(value)


class DateTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = date
    h5_dtype = np.dtype("datetime64[D]")

    def convert_to_attr(self, value: date):
        return str(value)

    def convert_from_attr(self, value: str):
        return date.fromisoformat(value)


class TimedeltaTypeHandler(AttrTypeHandler, RowTypeHandler):
    target_type = timedelta
    h5_dtype = np.dtype("timedelta64[us]")

    def convert_to_attr(self, value: timedelta):
        return value.total_seconds()

    def convert_from_attr(self, value: float):
        return timedelta(seconds=value)
