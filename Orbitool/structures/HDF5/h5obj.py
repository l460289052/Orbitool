from numpy.lib.arraysetops import union1d
from . import descriptor, memory_h5_location
import h5py
from typing import Union
from abc import abstractmethod


class _H5Obj:
    pass


descriptor.BaseHDF5Obj = _H5Obj


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


class H5Obj(_H5Obj):
    h5_type = descriptor.RegisterType("Object")

    _child_type_manager = ChildTypeManager()

    _export_value_names = {}

    def __init__(self, location: Union[h5py.Group, h5py.Dataset, memory_h5_location.Location], inited=True):
        self.location = location
        assert not inited or self.h5_type.attr_type_name == self.h5_type.type_name

    def __init_subclass__(cls):
        H5Obj._child_type_manager.add_type(cls.h5_type.type_name, cls)
        H5Obj._export_value_names[cls.h5_type.type_name] = {
            k: v for k, v in cls.__dict__.items() if issubclass(type(v), descriptor.Descriptor)}

    @classmethod
    def create_at(cls, location: Union[h5py.Group, memory_h5_location.Location], key):
        obj = cls(location.create_group(key), False)
        for name, desc in cls._export_value_names[obj.h5_type.type_name].items():
            desc.on_create(obj)
        return obj

    def initialize(self):
        pass

    @classmethod
    def descriptor(cls, name=None):
        return descriptor.H5ObjectDescriptor(cls, name)

    def to_memory(self):
        m_obj = type(self).create_at(memory_h5_location.Location(), 'mem')
        m_obj.copy_from(self)
        return m_obj

    def copy_from(self, another):
        for name, desc in self._export_value_names[self.h5_type.type_name].items():
            desc.copy_from_to(another, self)


H5Obj.__init_subclass__()
descriptor.BaseHDF5Obj = H5Obj


def infer_from(location: Union[h5py.Group, memory_h5_location.Location]):
    type_name = location.attrs['type']
    return H5Obj._child_type_maneger.get_type(type_name)(location)
