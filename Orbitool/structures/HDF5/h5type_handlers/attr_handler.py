from datetime import date, datetime

from ...base import *


class AttrHandler(StructureTypeHandler):
    @classmethod
    def write_to_h5(cls, args, h5group: Group, key: str, value):
        h5group.attrs[key] = value

    @classmethod
    def read_from_h5(cls, args, h5group: Group, key: str):
        return h5group.attrs[key]


class IntHandler(AttrHandler):
    @classmethod
    def validate(cls, value, args: tuple):
        return int(value)


class FloatHandler(AttrHandler):
    @classmethod
    def validate(cls, value, args: tuple):
        return float(value)


class BoolHandler(AttrHandler):
    @classmethod
    def validate(cls, value, args: tuple):
        return bool(value)


class StrHandler(AttrHandler):
    @classmethod
    def validate(cls, value, args: tuple):
        return str(value)


class DatetimeConverter(AttrHandler):
    @classmethod
    def write_to_h5(cls, args, h5group: Group, key: str, value: datetime):
        h5group.attrs[key] = str(value)

    @classmethod
    def read_from_h5(cls, args, h5group: Group, key: str):
        return datetime.fromisoformat(h5group.attrs[key])


class DateConverter(DatetimeConverter):
    @classmethod
    def read_from_h5(cls, args, h5group: Group, key: str):
        return date.fromisoformat(h5group.attrs[key])


