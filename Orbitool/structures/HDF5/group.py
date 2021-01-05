from . import descriptor
import h5py
import numpy as np
from abc import ABCMeta, abstractmethod
from typing import Union
import numpy as np

_types = {}
_names = {}


def add_type(name: str, typ: type):
    assert isinstance(name, str) and issubclass(typ, Group)
    assert name not in _types, f"type name `{name}` repeated, `{str(typ)}` and `{str(_types[name])}`"
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
    每个Group应该可以有一个不在文件中的副本，例如list在append的时候就可以先创建一个内存中的副本进去了
    需要的时候再通过其他方式挪到文件中。
    '''
    h5_type = descriptor.RegisterType("Group")

    def __init__(self, location: h5py.Group, inited=True):
        self.location = location
        assert not inited or self.h5_type.attr_type_name == self.h5_type.type_name

    def __init_subclass__(cls):
        add_type(cls.h5_type.type_name, cls)

    @classmethod
    @abstractmethod
    def create_at(cls, location: h5py.Group, key, *args, **kwargs):
        gp = cls(location.create_group(key), False)
        gp.h5_type.set_type_name()
        return gp

    @classmethod
    def descriptor(cls, name=None):
        return descriptor.GroupDescriptor(cls, name)


add_type(Group.h5_type.type_name, Group)


class Dict(Group):
    h5_type = descriptor.RegisterType("Dict")
    child_type: str = descriptor.ChildType()

    @classmethod
    def create_at(cls, child_type: type, *args, **kwargs):
        instance = super().create_at(*args, **kwargs)
        name = get_name(child_type)
        assert name is not None
        instance.child_type = name
        return instance

    @property
    def type_child_type(self):
        return get_type(self.child_type)

    def __getitem__(self, key):
        return self.type_child_type(self.location[key])

    def get_additem_location(self):
        return self.location

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

    index_dtype = np.dtype('S')
    @classmethod
    def create_at(cls, child_type: type, *args, **kwargs):
        instance = super().create_at(*args, **kwargs)
        name = get_name(child_type)
        assert name is not None
        instance.child_type = name
        instance.max_index = -1
        instance.sequence = np.array(tuple(), dtype=List.index_dtype)
        return instance

    @property
    def type_child_type(self):
        return get_type(self.child_type)

    def __getitem__(self, index: Union[int, slice]):
        indexes = self.sequence[index]
        if not isinstance(index, slice):
            indexes = (indexes,)
        location = self.location
        return list(map(self.type_child_type, (location[index] for index in indexes)))

    def get_append_location(self) -> (h5py.Group, str):
        self.max_index += 1
        index = str(self.max_index).encode('ascii')
        self.sequence = np.concatenate((self.sequence, (index,)))
        return self.location, index

    def __delitem__(self, index: Union[int, slice]):
        sequence = self.sequence
        slt = np.ones_like(sequence, dtype=bool)
        slt[index] = False
        location = self.location
        for ind in sequence[~slt]:
            del location[ind]
        self.sequence = sequence[slt]

    def get_insert_location(self, index):
        sequence = self.sequence
        part1 = sequence[:index]
        part2 = sequence[index:]
        self.max_index += 1
        index = str(self.max_index).encode('ascii')
        self.sequence = np.concatenate((part1, (index,), part2))
        return self.location, index

    def __iter__(self):
        location = self.location
        child_type = self.type_child_type
        for index in self.sequence:
            yield child_type(location[index])


__all__ = [k for k, v in globals().items() if isinstance(v, type)
           and issubclass(v, Group)]
