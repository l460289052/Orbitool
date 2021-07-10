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
        if value is None:
            return
        h5group.create_dataset(
            key, data=value, compression="gzip", compression_opts=1)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        if key not in h5group:
            return None
        return h5group[key][()]


single_types_converters: Dict[Type, BaseSingleConverter] = {
    bool: AttrConverter,
    int: AttrConverter,
    str: AttrConverter,
    float: AttrConverter,
    date: AttrConverter,
    datetime: DatetimeConverter,
    np.ndarray: NumpyConverter}


def register_converter(typ: Type, converter: Type[BaseSingleConverter]):
    single_types_converters[typ] = converter


class StructureConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: BaseStructure):
        if value is None:
            if key in h5group:
                del h5group[key]
            return

        if key not in h5group:
            group = h5group.create_group(key)
        else:
            group = h5group[key]

        for key, field in value.__fields__.items():
            shape_converters[field.shape].write_to_h5(
                group, key, field, getattr(value, key))

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        if key not in h5group:
            return None
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
        converter = single_types_converters.get(
            field.type_, StructureConverter)
        if value is None:
            if issubclass(converter, AttrConverter):
                if key in h5group.attrs:
                    del h5group.attrs[key]
            else:
                if key in h5group:
                    del h5group[key]
            return

        converter.write_to_h5(h5group, key, value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        converter = single_types_converters.get(
            field.type_, StructureConverter)
        if issubclass(converter, AttrConverter):
            if key not in h5group.attrs:
                return field.get_default()
        else:
            if key not in h5group:
                return field.get_default()
        return converter.read_from_h5(h5group, key)


class BaseListConverter:
    @staticmethod
    def write_to_h5(h5group: Group, key: str, values):
        pass

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        pass


class ListNdarrayConverter(BaseListConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, values):
        group = h5group.create_group(key)
        for i, value in enumerate(values):
            NumpyConverter.write_to_h5(group, str(i), value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        rets = []
        group: Group = h5group[key]
        for i in len(group):
            rets.append(NumpyConverter.read_from_h5(group, str(i)))
        return rets


class ListSimpleTypeConverter(BaseListConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, values):
        h5group.create_dataset(
            key, data=values, compression='gzip', compression_opts=1)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return list(h5group[key][()])


class ListDatetimeConverter(BaseListConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, values: List[datetime]):
        values = np.array(values, dtype='M8[s]').astype(int)
        h5group.create_dataset(
            key, data=values, compression='gzip', compression_opts=1)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        values = h5group[key][()]
        return list(values.astype('M8[s]').astype(datetime))


list_converters = {
    np.ndarray: ListNdarrayConverter,
    int: ListSimpleTypeConverter,
    float: ListSimpleTypeConverter,
    datetime: ListDatetimeConverter}


class ListConverter(BaseShapeConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, values: list):
        if key in h5group:
            del h5group[key]
        inner_type = get_args(field.outer_type_)[0]
        if inner_type in list_converters:
            list_converters[inner_type].write_to_h5(h5group, key, values)
        elif issubclass(inner_type, BaseTableItem):
            TableConverter.write_to_h5(h5group, key, inner_type, values)
        elif issubclass(inner_type, BaseStructure):
            group = h5group.create_group(key)
            for i, value in enumerate(values):
                StructureConverter.write_to_h5(group, str(i), value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        inner_type = get_args(field.outer_type_)[0]
        if key not in h5group:
            return field.get_default()
        if inner_type in list_converters:
            return list_converters[inner_type].read_from_h5(h5group, key)
        elif issubclass(inner_type, BaseTableItem):
            return TableConverter.read_from_h5(h5group, key, inner_type)
        elif issubclass(inner_type, BaseStructure):
            rets = []
            group: Group = h5group[key]
            for i in range(len(group)):
                rets.append(StructureConverter.read_from_h5(group, str(i)))
            return rets


class DictConverter(BaseShapeConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, field: ModelField, values: dict):
        if key in h5group:
            del h5group[key]
        inner_type = get_args(field.outer_type_)[1]
        if inner_type == np.ndarray:
            group = h5group.create_group(key)
            for index, value in enumerate(values.values()):
                NumpyConverter.write_to_h5(group, str(index), value)
        elif issubclass(inner_type, BaseStructure):
            group = h5group.create_group(key)
            for index, value in enumerate(values.values()):
                StructureConverter.write_to_h5(group, str(index), value)
        group.attrs["indexes"] = list(values.keys())

    @staticmethod
    def read_from_h5(h5group: Group, key: str, field: ModelField):
        key_type, inner_type = get_args(field.outer_type_)
        if key not in h5group:
            return field.get_default()
        rets = {}
        group: Group = h5group[key]
        keys = group.attrs["indexes"]
        if inner_type == np.ndarray:
            for index, key in enumerate(keys):
                rets[key_type(key)] = NumpyConverter.read_from_h5(
                    group, str(index))
        elif issubclass(inner_type, BaseStructure):
            for index, key in enumerate(keys):
                rets[key_type(key)] = StructureConverter.read_from_h5(
                    group, str(index))
        return rets


shape_converters: Dict[int, Type[SingleConverter]] = {
    SHAPE_SINGLETON: SingleConverter,
    SHAPE_LIST: ListConverter,
    SHAPE_DICT: DictConverter
}
