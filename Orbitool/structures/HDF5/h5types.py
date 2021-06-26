from datetime import datetime, date
from typing import Dict, List, Type
from abc import ABCMeta

import numpy as np
from h5py import Group
from pydantic.fields import (SHAPE_DICT, SHAPE_LIST, SHAPE_SET,
                             SHAPE_SINGLETON, ModelField)

from ..base import BaseStructure, structures


class BaseSingleConverter(metaclass=ABCMeta):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value): ...
    @staticmethod
    def read_from_h5(h5group: Group, key: str): ...


class AttrConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value):
        h5group.attrs[key] = value

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return h5group.attrs[key]


class DatetimeConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: datetime):
        h5group.attrs[key] = value.isoformat()

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return datetime.fromisoformat(h5group.attrs[key])


class DateConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: date):
        h5group.attrs[key] = value.isoformat()

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return date.fromisoformat(h5group.attrs[key])


class NumpyConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value):
        h5group.create_dataset(
            key, data=value, compression="gzip", compression_opts=1)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return h5group[key][:]


base_types_converters: Dict[Type, BaseSingleConverter] = {
    bool: AttrConverter,
    int: AttrConverter,
    str: AttrConverter,
    float: AttrConverter,
    date: AttrConverter,
    datetime: DatetimeConverter,
    np.ndarray: NumpyConverter}


class StructureConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: BaseStructure):
        if key in h5group:
            del h5group[key]
        group = h5group.create_group(key)

        for key, field in value.__fields__.items():
            shape_converters[field.shape].write_to_h5(
                group, key, field, getattr(value, key))

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        group = h5group[key]
        h5_type = structures.get_type(group.attrs["h5_type"])
        values = {}
        for key, field in h5_type.__fields__.items():
            values[key] = shape_converters[field.shape].read_from_h5(
                group, key, field)

        return h5_type(**values)


class BaseShapeConverter(metaclass=ABCMeta):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, value): ...
    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField): ...


class SingleConverter(BaseShapeConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, value):
        converter = base_types_converters.get(field.type_, StructureConverter)
        converter.write_to_h5(h5group, key, value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        converter = base_types_converters.get(field.type_, StructureConverter)
        return converter.read_from_h5(h5group, key)


class ListConverter(BaseShapeConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, value):
        pass

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        pass


class DictConverter(BaseShapeConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, value):
        pass

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        pass


shape_converters: Dict[int, Type[SingleConverter]] = {
    1: SingleConverter,
    2: ListConverter,
    4: DictConverter
}
