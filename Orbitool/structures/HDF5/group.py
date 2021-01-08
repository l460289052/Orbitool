from . import descriptor
import h5py
import numpy as np
from abc import ABCMeta, abstractmethod
from typing import Union
import numpy as np


class _Group:
    pass


class MemoryGroup:
    pass


descriptor.BaseHDF5Group = _Group


class ChildTypeManager:
    def __init__(self):
        self.types = {}
        self.names = {}

    def __set_name__(self, owner, name):
        self.base_type = owner

    def add_type(self, name: str, typ: type):
        assert isinstance(name, str) and issubclass(typ, self.base_type)
        assert name not in self.types, f"type name `{name}` repeated, `{str(typ)}` and `{str(self.types[name])}`"
        self.types[name] = typ
        self.names[typ] = name

    def get_type(self, name: str, default=None):
        return self.types.get(name, default)

    def get_name(self, typ: type, default=None):
        return self.names.get(typ, default)


class Group(_Group, metaclass=ABCMeta):
    '''
    以后可以加个缓存把所有location相同的都缓存一下
    每个Group应该可以有一个不在文件中的副本，例如list在append的时候就可以先创建一个内存中的副本进去了
    需要的时候再通过其他方式挪到文件中。
    '''
    h5_type = descriptor.RegisterType("Group")

    _child_type_maneger = ChildTypeManager()

    _export_value_names = {}
    _export_group_names = {}

    def __init__(self, location: h5py.Group, inited=True):
        self.location = location
        assert not inited or self.h5_type.attr_type_name == self.h5_type.type_name

    def __init_subclass__(cls):
        Group._child_type_maneger.add_type(cls.h5_type.type_name, cls)
        assert Group._export_value_names == cls._export_value_names, "`_export_names` shouldn't be replaced"
        Group._export_value_names[cls.h5_type.type_name] = [
            k for k, v in cls.__dict__.items() if issubclass(type(v), descriptor.Descriptor) and not issubclass(type(v), descriptor.GroupDescriptor)]
        Group._export_group_names[cls.h5_type.type_name] = [
            k for k, v in cls.__dict__.items() if issubclass(type(v), descriptor.GroupDescriptor)]

    @classmethod
    def create_at(cls, location: h5py.Group, key):
        gp = cls(location.create_group(key), False)
        gp.h5_type.set_type_name()

        for group_name in cls._export_group_names[gp.h5_type.type_name]:
            gd: descriptor.GroupDescriptor = cls.__dict__[group_name]
            sub_gp = gd.group_type.create_at(gp.location, gd.name)
            if gd.init:
                sub_gp.initialize(*gd.init_args)

        return gp

    def initialize(self):
        pass

    @classmethod
    def descriptor(cls, name=None):
        return descriptor.GroupDescriptor(cls, name)

    def to_memory(self) -> MemoryGroup:
        mg = MemoryGroup()
        for value_name in self._export_value_names[self.h5_type.type_name]:
            setattr(mg, value_name, getattr(self, value_name))
        for group_name in self._export_group_names[self.h5_type.type_name]:
            setattr(mg, group_name, getattr(self, group_name).to_memory())
        return mg

    def from_memory(self, mg: MemoryGroup):
        for value_name in self._export_value_names[self.h5_type.type_name]:
            setattr(self, value_name, getattr(mg, value_name))
        for group_name in self._export_group_names[self.h5_type.type_name]:
            getattr(self, group_name).from_memory(getattr(mg, group_name))


Group.__init_subclass__()


class Dict(Group):
    h5_type = descriptor.RegisterType("Dict")
    child_type: str = descriptor.ChildType()

    def initialize(self, child_type: type):
        name = self._child_type_maneger.get_name(child_type)
        assert name is not None
        self.child_type = name

    @property
    def type_child_type(self) -> Group:
        return self._child_type_maneger.get_type(self.child_type)

    def __getitem__(self, key):
        return self.type_child_type(self.location[key])

    def additem(self, key):
        return self.type_child_type.create_at(self.location, key)

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

    @classmethod
    def descriptor(cls, child_type: type, name=None):
        return descriptor.GroupDescriptor(cls, name, True, (child_type, ))


class List(Group):
    h5_type = descriptor.RegisterType("List")
    child_type: str = descriptor.ChildType()
    sequence = descriptor.SmallNumpy()
    max_index = descriptor.Int()

    index_dtype = np.dtype('S')

    def initialize(self, child_type: type):
        name = self._child_type_maneger.get_name(child_type)
        assert name is not None
        self.child_type = name
        self.max_index = -1
        self.sequence = np.array(tuple(), dtype=List.index_dtype)

    @property
    def type_child_type(self) -> Group:
        return self._child_type_maneger.get_type(self.child_type)

    def __getitem__(self, index: Union[int, slice]):
        true_index = self.sequence[index]
        location = self.location
        if not isinstance(index, slice):
            return self.type_child_type(location[true_index])
        return list(map(self.type_child_type, (location[index] for index in true_index)))

    def append(self):
        self.max_index += 1
        index = str(self.max_index).encode('ascii')
        self.sequence = np.concatenate((self.sequence, (index,)))
        return self.type_child_type.create_at(self.location, index)

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
        index = str(self.max_index).encode('ascii')
        self.sequence = np.concatenate((part1, (index,), part2))
        return self.type_child_type.create_at(self.location, index)

    def __iter__(self):
        location = self.location
        child_type = self.type_child_type
        for index in self.sequence:
            yield child_type(location[index])

    @classmethod
    def descriptor(cls, child_type: type, name=None):
        return descriptor.GroupDescriptor(cls, name, True, (child_type, ))


__all__ = [k for k, v in globals().items() if isinstance(v, type)
           and issubclass(v, Group)]
