from . import descriptor, memory_h5_location, h5obj
import h5py
import numpy as np
from abc import ABCMeta, abstractmethod
from typing import Union
import numpy as np


class Group(h5obj.H5Obj):
    '''
    以后可以加个缓存把所有location相同的都缓存一下
    每个Group应该可以有一个不在文件中的副本，例如list在append的时候就可以先创建一个内存中的副本进去了
    需要的时候再通过其他方式挪到文件中。
    '''
    h5_type = descriptor.RegisterType("Group")


class Dict(Group):
    h5_type = descriptor.RegisterType("Dict")
    child_type: str = descriptor.ChildType()

    def initialize(self, child_type: type):
        name = self._child_type_manager.get_name(child_type)
        assert name is not None
        self.child_type = name

    @property
    def type_child_type(self) -> Group:
        return self._child_type_manager.get_type(self.child_type)

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
    def descriptor(cls, child_type: Union[type, str], name=None):
        return descriptor.H5ObjectDescriptor(cls, name, True, (child_type, ))

    def copy_from(self, another):
        super().copy_from(another)
        location = self.location
        chlid_type = self.type_child_type
        for k, v in another.items():
            child = chlid_type.create_at(location, k)
            child.copy_from(v)


class List(Group):
    h5_type = descriptor.RegisterType("List")
    child_type: str = descriptor.ChildType()
    sequence = descriptor.SmallNumpy()
    max_index = descriptor.Int()

    index_dtype = np.dtype('S')

    def initialize(self, child_type: type):
        name = self._child_type_manager.get_name(child_type)
        assert name is not None
        self.child_type = name
        self.max_index = -1
        self.sequence = np.array(tuple(), dtype=List.index_dtype)

    @property
    def type_child_type(self) -> Group:
        return self._child_type_manager.get_type(self.child_type)

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
    def descriptor(cls, child_type: Union[type, str], name=None):
        return descriptor.H5ObjectDescriptor(cls, True, (child_type, ), name=name)

    def copy_from(self, another):
        super().copy_from(another)
        location_s = self.location
        location_a = another.location
        child_type = self.type_child_type
        for index in another.sequence:
            child = child_type.create_at(location_s, index)
            child.copy_from(child_type(location_a[index]))


__all__ = [k for k, v in globals().items() if isinstance(v, type)
           and issubclass(v, Group)]
