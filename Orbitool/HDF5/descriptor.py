from abc import ABCMeta
from datetime import datetime

import numpy as np

BaseHDF5Group = None

class Descriptor(metaclass=ABCMeta):
    def __init__(self, name=None):
        self.name = name

    def __set_name__(self, owner, name):
        assert issubclass(
            owner, BaseHDF5Group), "Owner class must be a subclass of `HDF5Group`"
        if self.name is None:
            self.name = name


class Attr(Descriptor):
    '''
    属性也可以考虑加入缓存机制，就是如果obj和name一样的话
    '''

    def __get__(self, obj, objtype=None):
        return obj.location.attrs.get(self.name, None)

    def __set__(self, obj, value):
        obj.location.attrs[self.name] = value


class Dataset(Descriptor):
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


class Int(Attr):
    pass


class Str(Attr):
    pass


class Float(Attr):
    pass


class Datetime(Attr):
    def __get__(self, *args):
        ret = super().__get__(*args)
        return np.datetime64(ret).astype(datetime)

    def __set__(self, obj, value: datetime):
        super().__set__(obj, value.isoformat())


class SmallNumpy(Attr):
    pass


class BigNumpy(Dataset):
    pass


class RegisterType(Str):
    def __init__(self, type_name: str):
        super().__init__("type")
        self.type_name = type_name

    def __set__(self, obj, value):
        raise NotImplementedError()

    def __get__(self, obj, objtype):
        return MainTypeHandler(self.name, obj, self.type_name)


class MainTypeHandler:
    def __init__(self, name, obj, type_name):
        self.name = name
        self.obj = obj
        self.type_name = type_name

    def set_type_name(self):
        self.obj.location.attrs[self.name] = self.type_name

    @property
    def attr_type_name(self):
        return self.obj.location.attrs.get(self.name, None)


class ChildType(Str):
    pass


class GroupDescriptor(Descriptor):
    def __init__(self, group_type: type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_type = group_type

    def __get__(self, obj, objtype):
        self.group_type(obj.location[self.name])


__all__ = [k for k, v in globals().items() if issubclass(
    v, (Descriptor, MainTypeHandler))]
