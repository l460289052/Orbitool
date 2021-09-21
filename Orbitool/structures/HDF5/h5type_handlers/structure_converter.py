from h5py import Group

from .base import (
    BaseStructure, TypeHandler, get_default, get_handler_args,
    register_handler, structures)
from .attr_converter import AttrHandler

H5_TYPE = "h5_type"


class StructureHandler(TypeHandler):
    @classmethod
    def write_to_h5(cls, args, h5group: Group, key: str, value: BaseStructure):
        if key not in h5group:
            group = h5group.create_group(key)
        else:
            group = h5group[key]

        for key, field in value.__dataclass_fields__.items():
            handler, handler_args = get_handler_args(field.type)
            v = getattr(value, key)
            if v is None:
                if issubclass(handler, AttrHandler):
                    if key in group.attrs:
                        del group.attrs[key]
                else:
                    if key in group:
                        del group[key]
                continue
            handler.write_to_h5(handler_args, group, key, getattr(value, key))
        group.attrs[H5_TYPE] = value.h5_type

    @classmethod
    def read_from_h5(cls, args, h5group: Group, key: str):
        if key not in h5group:
            return None

        group = h5group[key]
        h5_type: BaseStructure = structures.get_type(group.attrs[H5_TYPE])
        values = []
        for key, field in h5_type.__dataclass_fields__.items():
            handler, handler_args = get_handler_args(field.type)
            if issubclass(handler, AttrHandler):
                if key not in group.attrs:
                    v = get_default(field)
                    values.append(v)
                    continue
            elif key not in group:
                v = get_default(field)
                values.append(v)
                continue
            values.append(handler.read_from_h5(handler_args, group, key))
        return h5_type(*values)
