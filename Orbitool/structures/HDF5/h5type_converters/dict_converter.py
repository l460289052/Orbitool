
from typing import Dict, List, Type, get_args

import numpy as np
from h5py import Group
from pydantic.fields import SHAPE_DICT, ModelField

from ...base import BaseStructure
from .converters import (BaseShapeConverter, StructureConverter,
                         register_shape_converter)
from .single_converters import NumpyConverter


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


register_shape_converter(SHAPE_DICT, DictConverter)
