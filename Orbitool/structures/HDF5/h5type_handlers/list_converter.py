from typing import List
from datetime import datetime

import numpy as np
from h5py import Group

from .base import *


class ListHandler(TypeHandler, List):
    @classmethod
    def write_to_h5(cls, args: tuple, h5group: Group, key: str, value):
        if key in h5group:
            del h5group[key]
        inner_type = args[0]
        if inner_type in (int, float):
            h5group.create_dataset(key, dtype=inner_type, data=value)
        elif inner_type is datetime:
            value = np.array(value, dtype='M8[s]').astype(int)
            h5group.create_dataset(key, dtype=int, data=value)
        else:
            group = h5group.create_group(key)
            handler, handler_args = get_handler_args(inner_type)
            for i, v in enumerate(value):
                handler.write_to_h5(handler_args, group, str(i), v)
        return super().write_to_h5(args, h5group, key, value)

    @classmethod
    def read_from_h5(cls, args: tuple, h5group: Group, key: str):
        inner_type = args[0]
        if inner_type in (int, float):
            return list(map(inner_type, h5group[key][()]))
        elif inner_type is datetime:
            value = h5group[key][()]
            return list(value.astype('M8[s]').astype(datetime))
        else:
            group = h5group[key]
            handler, handler_args = get_handler_args(inner_type)
            return [handler.read_from_h5(handler_args, group, str(i)) for i in range(len(group))]
