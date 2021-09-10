from datetime import datetime
from typing import List, get_args

from pydantic.fields import SHAPE_LIST, ModelField
import numpy as np
from h5py import Group

from ...base import BaseStructure, BaseTableItem
from ..h5datatable import TableConverter
from .converters import BaseShapeConverter, StructureConverter, register_shape_converter
from .single_converters import NumpyConverter


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


register_shape_converter(SHAPE_LIST, ListConverter)
