import h5py
import numpy as np
import io
from abc import ABCMeta, abstractmethod
import datetime
from typing import Optional, Union
import numpy as np


class HDF5Descriptor(metaclass=ABCMeta):
    def __init__(self, name=None):
        self.name = name

    def __set_name__(self, owner, name):
        assert issubclass(
            owner, _HDF5Group), "Owner class must be a subclass of `HDF5Group`"
        if self.name is None:
            self.name = name


class HDF5Attr(HDF5Descriptor):
    '''
    属性也可以考虑加入缓存机制，就是如果obj和name一样的话
    '''

    def __get__(self, obj, objtype=None):
        return obj.location.attrs.get(self.name, None)

    def __set__(self, obj, value):
        obj.location.attrs[self.name] = value


class HDF5Dataset(HDF5Descriptor):
    def __get__(self, obj, objtype=None):
        dataset = obj.location.get(self.name, None)
        if dataset is None:
            return None
        ret = np.empty(dataset.shape, dtype=dataset.dtype)
        dataset.read_direct(ret)
        return ret

    def __set__(self, obj, value):
        obj.location.create_dataset(
            self.name, shape=value.shape, dtype=value.dtype,)
        obj.location[self.name] = value


class HDF5Int(HDF5Attr):
    pass


class HDF5Str(HDF5Attr):
    pass


class HDF5Float(HDF5Attr):
    pass


class HDF5Datetime(HDF5Attr):
    def __get__(self, *args):
        ret = super().__get__(*args)
        return np.datetime64(ret).astype(datetime.datetime)

    def __set__(self, obj, value: datetime.datetime):
        super().__set__(obj, value.isoformat())


class HDF5SmallNumpy(HDF5Attr):
    pass


class HDF5BigNumpy(HDF5Dataset):
    pass


_hdf5types = {}
_hdf5names = {}


def add_hdf5_type(name: str, typ: type):
    assert isinstance(name) and issubclass(typ, HDF5Group)
    assert name not in _hdf5names, f"type name `{name}` repeated, `{str(typ)}` and `{str(_hdf5types[name])}`"
    _hdf5types[name] = typ
    _hdf5names[typ] = name


def get_hdf5_type(name: str, default=None):
    return _hdf5types.get(name, default)


def get_hdf5_name(typ: type, default=None):
    return _hdf5names.get(typ, default)


class HDF5RegisterType(HDF5Str):
    def __init__(self, type_name: str):
        super().__init__("type")
        self.type_name = type_name

    def __set__(self, obj, value):
        raise NotImplementedError()

    def __get__(self, obj, objtype):
        return HDF5MainTypeHandler(self.name, obj, self.type_name)


class HDF5MainTypeHandler:
    def __init__(self, name, obj, type_name):
        self.name = name
        self.obj = obj
        self.type_name = type_name

    def set_type_name(self):
        self.obj.location.attrs[self.name] = self.type_name

    @property
    def attr_type_name(self):
        return self.obj.location.attrs.get(self.name, None)


class HDF5ChildType(HDF5Str):
    pass


class HDF5GroupDescriptor(HDF5Descriptor):
    def __init__(self, group_type: type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_type = group_type

    def __get__(self, obj, objtype):
        self.group_type(obj.location[self.name])


class _HDF5Group:
    pass


class HDF5Group(_HDF5Group, metaclass=ABCMeta):
    '''
    以后可以加个缓存把所有location相同的都缓存一下
    '''
    h5_type = HDF5RegisterType("Group")

    def __init__(self, location: h5py.Group):
        self.location = location

        if self.h5_type.attr_type_name is None:
            self.init_group()

    def __init_subclass__(cls):
        add_hdf5_type(cls.h5_type.type_name, cls)

    @abstractmethod
    def init_group(self):
        self.h5_type.set_type_name()

    @classmethod
    def descriptor(cls, name=None):
        return HDF5GroupDescriptor(cls, name)


add_hdf5_type(HDF5Group.h5_type.type_name, HDF5Group)


class HDF5Dict(HDF5Group):
    h5_type = HDF5RegisterType("Dict")
    child_type: str = HDF5ChildType()

    def __init__(self, child_type: type = None, *args, **kwargs):
        self.type_child_type = child_type
        super().__init__(*args, **kwargs)
        assert self.child_type == get_hdf5_name(self.type_child_type)

    def init_group(self):
        super().init_group()
        self.child_type = get_hdf5_name(self.type_child_type)

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


class HDF5List(HDF5Group):
    h5_type = HDF5RegisterType("List")
    child_type: str = HDF5ChildType()
    sequence = HDF5SmallNumpy()
    max_index = HDF5Int()

    def __init__(self, child_type: type = None, *args, **kwargs):
        self.type_child_type = child_type
        super().__init__(*args, **kwargs)
        assert self.child_type == get_hdf5_name(self.type_child_type)

    def init_group(self):
        super().init_group()
        self.child_type = get_hdf5_name(self.type_child_type)
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


class Spectrum(HDF5Group):
    mz = HDF5BigNumpy()
    start_time = HDF5Datetime()
    inta = HDF5Int()
    floata = HDF5Float()
    smallnp = HDF5SmallNumpy()


# if __name__ == "__main__":
    # h5 = h5py.File("tmp.hdf5", 'w')
    # spectrum = Spectrum(h5.create_group('spectrum'))

    # spectrum.start_time = datetime.datetime.now()
    # spectrum.mz = np.random.rand(10)
    # spectrum.mz = np.random.rand(20)
    # spectrum.inta = 4
    # assert spectrum.inta == 4
    # spectrum.floata = 4.0
    # assert spectrum.floata == 4.0
    # print(spectrum.start_time)
    # print(spectrum.mz)
