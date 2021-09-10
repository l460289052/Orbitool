from abc import ABCMeta
from typing import Dict, List, Type, get_args

from h5py import Group
from pydantic.fields import SHAPE_SINGLETON, ModelField

from ...base import BaseStructure, structures


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


single_types_converters: Dict[Type, BaseSingleConverter] = {}


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


shape_converters: Dict[int, Type[SingleConverter]] = {
    SHAPE_SINGLETON: SingleConverter
}


def register_shape_converter(shape: int, converter: Type[SingleConverter]):
    shape_converters[shape] = converter
