import abc
from datetime import date, datetime
from typing import Any, final

from h5py import string_dtype
import numpy as np

from .base import *


class IntHandler(AttrTypeHandler):
    target_type = int

    def convert_to_h5(self, value):
        return int(value)

    def convert_from_h5(self, value):
        return int(value)


class FloatHandler(AttrTypeHandler):
    target_type = float

    def convert_to_h5(self, value):
        return float(value)

    def convert_from_h5(self, value):
        return float(value)


class BoolHandler(AttrTypeHandler):
    target_type = bool

    def convert_to_h5(self, value):
        return bool(value)

    def convert_from_h5(self, value):
        return bool(value)


class StrHandler(AttrTypeHandler):
    target_type = str

    def convert_to_h5(self, value):
        return str(value)

    def convert_from_h5(self, value):
        if isinstance(value, bytes):
            return value.decode()
        return value


class DatetimeConverter(AttrTypeHandler):
    target_type = datetime

    def convert_to_h5(self, value: datetime):
        return str(value)

    def convert_from_h5(self, value: str):
        return datetime.fromisoformat(value)


class DateConverter(AttrTypeHandler):
    target_type = date

    def convert_to_h5(self, value: date):
        return str(value)

    def convert_from_h5(self, value: str):
        return date.fromisoformat(value)
