
from typing import Dict, List, Tuple
from .base import *
from .simple_handler import AttrHandler

H5_TYPE = "h5_type"


class StructureHandler(StructureTypeHandler):
    def write_to_h5(self, h5group: Group, key: str, value):
        if key in h5group:
            del h5group[key]

        group = h5group.create_group(key)

        for key, field in value.__dataclass_fields__.items():
            handler: StructureTypeHandler = get_handler(field.type)
            v = getattr(value, key)
            if v is None:
                continue
            handler.write_to_h5(group, key, v)
        group.attrs[H5_TYPE] = value.h5_type

    def read_from_h5(self, h5group: Group, key: str):
        if key not in h5group:
            return None

        group = h5group[key]
        h5_type: BaseStructure = structures.get_type(group.attrs[H5_TYPE])
        values = []
        for key, field in h5_type.__dataclass_fields__.items():
            handler: StructureTypeHandler = get_handler(field.type)
            if isinstance(handler, AttrHandler):
                if key not in group.attrs:
                    v = get_default(field)
                    values.append(v)
                    continue
            elif key not in group:
                v = get_default(field)
                values.append(v)
                continue
            try:
                values.append(handler.read_from_h5(group, key))
            except:
                brokens.append('/'.join((h5group.name, key)))
                values.append(get_default(field))

        return h5_type(*values)


brokens: List[Tuple[str, str]] = []
