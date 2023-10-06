from datetime import date, datetime, timedelta

# from h5py import string_dtype
import numpy as np

from .base import *


class IntTypeHandler(AttrTypeHandler):
    target_type = int

    def convert_to_attr(self, value):
        return int(value)

    def convert_from_attr(self, value):
        return int(value)


class FloatTypeHandler(AttrTypeHandler):
    target_type = float

    def convert_to_attr(self, value):
        return float(value)

    def convert_from_attr(self, value):
        return float(value)


class BoolTypeHandler(AttrTypeHandler):
    target_type = bool

    def convert_to_attr(self, value):
        return bool(value)

    def convert_from_attr(self, value):
        return bool(value)


class StrTypeHandler(AttrTypeHandler):
    target_type = str

    def convert_to_attr(self, value):
        return str(value)

    def convert_from_attr(self, value):
        return value

class BytesTypeHandler(AttrTypeHandler):
    target_type = bytes
    def convert_to_attr(self, value):
        return value
    
    def convert_from_attr(self, value):
        return value

class DatetimeTypeHandler(AttrTypeHandler):
    target_type = datetime

    def convert_to_attr(self, value: datetime):
        return str(value)

    def convert_from_attr(self, value: str):
        return datetime.fromisoformat(value)


class DateTypeHandler(AttrTypeHandler):
    target_type = date

    def convert_to_attr(self, value: date):
        return str(value)

    def convert_from_attr(self, value: str):
        return date.fromisoformat(value)


class TimedeltaTypeHandler(AttrTypeHandler):
    target_type = timedelta

    def convert_to_attr(self, value: timedelta):
        return value.total_seconds()

    def convert_from_attr(self, value: float):
        return timedelta(seconds=value)
