
from typing import Dict, List, Type, get_args

import numpy as np
from h5py import Group

from .base import *


class DictHandler(TypeHandler):
    @classmethod
    def write_to_h5(cls, args: tuple, h5group: Group, key: str, value: dict):
        if key in h5group:
            del h5group[key]
        group = h5group.create_group(key)
        inner_type = args[1]
        handler, handler_args = get_handler_args(inner_type)
        for index, v in enumerate(value.values()):
            handler.write_to_h5(handler_args, group, str(index), v)
        group.attrs["indexes"] = list(value.keys())

    @classmethod
    def read_from_h5(cls, args: tuple, h5group: Group, key: str):
        rets = {}
        key_type, inner_type = args
        group: Group = h5group[key]
        keys = group.attrs["indexes"]
        handler, handler_args = get_handler_args(inner_type)
        return {key_type(key): handler.read_from_h5(handler_args, group, str(index)) for index, key in enumerate(keys)}


register_handler(dict, DictHandler)
