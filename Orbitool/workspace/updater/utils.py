import imp
from typing import Iterable, Type
import h5py
import numpy as np


def write_to(h5obj: h5py.Group, name: str, data: np.ndarray):
    if name in h5obj:
        del h5obj[name]
    h5obj.create_dataset(
        name, data=data, compression="gzip", compression_opts=1)


def move_to(h5obj: h5py.Group, source: str, target: str):
    if source in h5obj:
        if target in h5obj:
            del h5obj[target]
        h5obj.move(source, target)


def copy_to(h5obj: h5py.Group, source: str, target: str):
    if source in h5obj:
        if target in h5obj:
            del h5obj[target]
        h5obj.copy(source, target)


def create_group(h5obj: h5py.Group, name: str):
    name = str(name)
    if name in h5obj:
        del h5obj[name]
    return h5obj.create_group(name)


def write_dict_keys(h5obj: h5py.Group, name: str, keys: Iterable):
    name = str(name)
    if name in h5obj:
        del h5obj[name]
    group = h5obj.create_group(name)
    group.attrs["indexes"] = list(map(str, keys))
    return group


def read_dict_keys(h5obj: h5py.Group, name: str, key_type: Type = str):
    if name not in h5obj:
        return []
    group: h5py.Group = h5obj[name]
    keys = group.attrs["indexes"]
    return list(map(key_type, keys))


def read_dict(h5obj: h5py.Group, name: str, key_type: Type = str):
    """
        yield group, str(index), key
    """
    if name not in h5obj:
        return
    group: h5py.Group = h5obj[name]
    keys = group.attrs["indexes"]
    for index, key in enumerate(keys):
        yield group, index, key_type(key)
