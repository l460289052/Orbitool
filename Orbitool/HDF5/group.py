from . import descriptor
import h5py
import numpy as np
from abc import ABCMeta, abstractmethod
from typing import Union
import numpy as np

_types = {}
_names = {}


def add_type(name: str, typ: type):
    assert isinstance(name) and issubclass(typ, Group)
    assert name not in _names, f"type name `{name}` repeated, `{str(typ)}` and `{str(_types[name])}`"
    _types[name] = typ
    _names[typ] = name


def get_type(name: str, default=None):
    return _types.get(name, default)


def get_name(typ: type, default=None):
    return _names.get(typ, default)


class _Group:
    pass


descriptor.BaseHDF5Group = _Group


class Group(_Group, metaclass=ABCMeta):
    '''
    以后可以加个缓存把所有location相同的都缓存一下
    '''
    h5_type = descriptor.RegisterType("Group")

    def __init__(self, location: h5py.Group):
        self.location = location

        if self.h5_type.attr_type_name is None:
            self.init_group()

    def __init_subclass__(cls):
        add_type(cls.h5_type.type_name, cls)

    @abstractmethod
    def init_group(self):
        self.h5_type.set_type_name()

    @classmethod
    def descriptor(cls, name=None):
        return descriptor.GroupDescriptor(cls, name)


add_type(Group.h5_type.type_name, Group)


class Dict(Group):
    h5_type = descriptor.RegisterType("Dict")
    child_type: str = descriptor.ChildType()

    def __init__(self, child_type: type = None, *args, **kwargs):
        self.type_child_type = child_type
        super().__init__(*args, **kwargs)
        assert self.child_type == get_name(self.type_child_type)

    def init_group(self):
        super().init_group()
        self.child_type = get_name(self.type_child_type)

    def __getitem__(self, key):
        return self.type_child_type(self.location[key])

    def additem(self, key):
        return self.type_child_type(self.location.create_group(key))

    def __delitem__(self, key):
        del self.location[key]

    def items(self):
        for k, v in self.location.items():
            yield k, self.type_child_type(v)

    def keys(self):
        return self.location.keys()

    def values(self):
        for v in self.location.values():
            yield self.type_child_type(v)


class List(Group):
    h5_type = descriptor.RegisterType("List")
    child_type: str = descriptor.ChildType()
    sequence = descriptor.SmallNumpy()
    max_index = descriptor.Int()

    def __init__(self, child_type: type = None, *args, **kwargs):
        self.type_child_type = child_type
        super().__init__(*args, **kwargs)
        assert self.child_type == get_name(self.type_child_type)

    def init_group(self):
        super().init_group()
        self.child_type = get_name(self.type_child_type)
        self.max_index = -1
        self.sequence = np.array(tuple(), dtype=str)

    def __getitem__(self, index: Union[int, slice]):
        indexes = self.sequence[index]
        if not isinstance(index, slice):
            indexes = (indexes,)
        location = self.location
        return list(map(self.type_child_type, (location[index] for index in indexes)))

    def append(self):
        self.max_index += 1
        index = str(self.max_index)
        self.sequence = np.concatenate((self.sequence, (index,)))
        return self.type_child_type(self.location.create_group(index))

    def __delitem__(self, index: Union[int, slice]):
        sequence = self.sequence
        slt = np.ones_like(sequence, dtype=bool)
        slt[index] = False
        location = self.location
        for ind in sequence[~slt]:
            del location[ind]
        self.sequence = sequence[slt]

    def insert(self, index):
        sequence = self.sequence
        part1 = sequence[:index]
        part2 = sequence[index:]
        self.max_index += 1
        index = str(self.max_index)
        self.sequence = np.concatenate((part1, (index,), part2))
        return self.type_child_type(self.location.create_group(index))


__all__ = [k for k, v in globals().items() if issubclass(v, Group)]
