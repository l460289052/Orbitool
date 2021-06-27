from datetime import datetime, date
from typing import Dict, List, Type, get_args
from abc import ABCMeta

import numpy as np
from h5py import Group
from pydantic.fields import (SHAPE_DICT, SHAPE_LIST, SHAPE_SET,
                             SHAPE_SINGLETON, ModelField)

from ..base import BaseStructure, structures, BaseTableItem
from .h5datatable import TableConverter


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
    def write_to_h5(h5group: Group, key: str, field: ModelField, values: list):
        inner_type = get_args(field.outer_type_)
        if inner_type == np.ndarray:
            group = h5group.create_group(key)
            for i, value in enumerate(values):
                NumpyConverter.write_to_h5(group, str(i), value)
        elif issubclass(inner_type, BaseTableItem):
            TableConverter.write_to_h5(h5group, key, inner_type, values)
        elif issubclass(inner_type, BaseStructure):
            group = h5group.create_group(key)
            for i, value in enumerate(values):
                StructureConverter.write_to_h5(group, str(i), value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        inner_type = get_args(field.outer_type_)
        if inner_type == np.ndarray:
            rets = []
            group: Group = h5group[key]
            for i in len(group):
                rets.append(NumpyConverter.read_from_h5(group, str(i)))
            return rets
        elif issubclass(inner_type, BaseTableItem):
            return TableConverter.read_from_h5(h5group, key, inner_type)
        elif issubclass(inner_type, BaseStructure):
            rets = []
            group: Group = h5group[key]
            for i in len(group):
                rets.append(StructureConverter.read_from_h5(group, str(i)))


class DictConverter(BaseShapeConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, values: dict):
        inner_type = get_args(field.outer_type_)[1]
        if inner_type == np.ndarray:
            group = h5group.create_group(key)
            for key, value in values.items():
                NumpyConverter.write_to_h5(group, str(key), value)
        elif issubclass(inner_type, BaseStructure):
            group = h5group.create_group(key)
            for key, value in values.items():
                StructureConverter.write_to_h5(group, str(key), value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        key_type, inner_type = get_args(field.outer_type_)
        if inner_type == np.ndarray:
            rets = {}
            group: Group = h5group[key]
            for key in group.keys():
                rets[key_type(key)] = NumpyConverter.read_from_h5(group, key)
            return rets
        elif issubclass(inner_type, BaseStructure):
            rets = {}
            group: Group = h5group[key]
            for key in group.keys():
                rets[key_type(key)] = StructureConverter.read_from_h5(
                    group, key)
            return rets


shape_converters: Dict[int, Type[SingleConverter]] = {
    SHAPE_SINGLETON: SingleConverter,
    SHAPE_LIST: ListConverter,
    SHAPE_DICT: DictConverter
}
