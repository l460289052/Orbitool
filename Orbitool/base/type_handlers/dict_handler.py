
import numpy as np

from .base import *

# TODO

class DictHandler(StructureTypeHandler):
    def __init__(self, args) -> None:
        super().__init__(args=args)
        self.key_type = self.args[0]
        self.inner_type = self.args[1]

    def write_to_h5(self, h5group: Group, key: str, value: dict):
        if key in h5group:
            del h5group[key]
        group = h5group.create_group(key)
        inner_type = self.inner_type
        handler: StructureTypeHandler = get_handler(inner_type)
        for index, v in enumerate(value.values()):
            handler.write_to_h5(group, str(index), v)
        group.attrs["indexes"] = list(map(str, value.keys()))

    def read_from_h5(self, h5group: Group, key: str):
        key_type, inner_type = self.key_type, self.inner_type
        group: Group = h5group[key]
        keys = group.attrs["indexes"]
        handler: StructureTypeHandler = get_handler(inner_type)
        return {key_type(key): handler.read_from_h5(group, str(index)) for index, key in enumerate(keys)}
