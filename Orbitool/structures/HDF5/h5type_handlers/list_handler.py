from typing import List
from datetime import datetime

import numpy as np

from .base import *


class ListHandler(StructureTypeHandler, List):
    def __init__(self, args) -> None:
        super().__init__(args)
        self.inner_type = args[0]

    def write_to_h5(self, h5group: Group, key: str, value):
        if key in h5group:
            del h5group[key]
        inner_type = self.inner_type
        if inner_type in (int, float):
            h5group.create_dataset(key, dtype=inner_type, data=value)
        elif inner_type is datetime:
            value = np.array(value, dtype='M8[s]').astype(int)
            h5group.create_dataset(key, dtype=int, data=value)
        else:
            group = h5group.create_group(key)
            handler: StructureTypeHandler = get_handler(inner_type)
            if isinstance(inner_type, type):
                assert not issubclass(inner_type, BaseRowItem), "Please use Row[{0}] instead of List[{0}] in {1}".format(
                    inner_type, h5group.name + key)
            for i, v in enumerate(value):
                handler.write_to_h5(group, str(i), v)

    def read_from_h5(self, h5group: Group, key: str):
        inner_type = self.inner_type
        if inner_type in (int, float):
            return list(map(inner_type, h5group[key][()]))
        elif inner_type is datetime:
            value = h5group[key][()]
            return list(value.astype('M8[s]').astype(datetime))
        else:
            group = h5group[key]
            handler: StructureTypeHandler = get_handler(inner_type)
            return [handler.read_from_h5(group, str(i)) for i in range(len(group))]
