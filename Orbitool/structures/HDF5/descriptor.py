from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Union, List, Tuple

import numpy as np

BaseHDF5Obj = None


def get_type(name: str) -> type:
    global get_type
    get_type = BaseHDF5Obj._child_type_manager.get_type
    return get_type(name)


def get_name(typ: type) -> str:
    global get_name
    get_name = BaseHDF5Obj._child_type_manager.get_name
    return get_name(typ)


class Descriptor(metaclass=ABCMeta):
    def __init__(self, name=None):
        self.name: str = name
        self.descriptor_name = None

    def __set_name__(self, owner, name):
        assert issubclass(
            owner, BaseHDF5Obj), "Owner class must be a subclass of `HDF5Group`"
        if self.name is None:
            self.name = name
        self.descriptor_name = name
        # elif self.name.endswith('/'):
        #     self.name += name

    @abstractmethod
    def __set__(self, obj, value):
        pass

    @abstractmethod
    def __get__(self, obj, objtype=None):
        pass

    def copy_from_to(self, obj_src, obj_dst):
        self.__set__(obj_dst, self.__get__(obj_src))

    def on_create(self, obj):
        pass


class Attr(Descriptor):
    '''
    属性也可以考虑加入缓存机制，就是如果obj和name一样的话
    '''

    def __get__(self, obj, objtype=None):
        return obj.location.attrs.get(self.name, None)

    def __set__(self, obj, value):
        obj.location.attrs[self.name] = value


class SimpleDataset(Descriptor):
    """
    numpy.ndarray in hdf5, please read to memory before frequent access.
    for i in ins.simpleDataset:
        pass        (x)
    for i in ins.simpleDataset[:]:
        pass        (v)
    """
    kwargs = dict(compression='gzip', compression_opts=1)

    def __get__(self, obj, objtype=None):
        return obj.location.get(self.name, None)

    def __set__(self, obj, value):
        if self.name in obj.location:
            del obj.location[self.name]
        obj.location.create_dataset(
            self.name, data=value, **SimpleDataset.kwargs)

    # def generate_attr(self, attr_type: type, name=None):
    #     assert issubclass(attr_type, Attr)
    #     return attr_type('/'.join((self.name, name)) if name is not None else self.name+'/')


class Bool(Attr):
    pass


class Int(Attr):
    pass


class Str(Attr):
    pass


class Float(Attr):
    pass


class Datetime(Str):
    dateFormat = r"%Y-%m-%d %H:%M:%S"
    @classmethod
    def strftime(cls, datetime):
        return datetime.strftime(Datetime.dateFormat)

    @classmethod
    def strptime(cls, s):
        return datetime.strptime(s, Datetime.dateFormat)

    def __get__(self, *args):
        return Datetime.strptime(super().__get__(*args))

    def __set__(self, obj, value: datetime):
        super().__set__(obj, Datetime.strftime(value))


class TimeDelta(Float):
    def __get__(self, *args):
        ret = super().__get__(*args)
        return timedelta(seconds=ret)

    def __set__(self, obj, value: timedelta):
        return super().__set__(obj, value.total_seconds())


class SmallNumpy(Attr):
    pass


class BigNumpy(SimpleDataset):
    pass


class RegisterType(Str):
    def __init__(self, type_name: str, obj=None):
        super().__init__("type")
        self.type_name = type_name
        self.obj = obj

    def __set__(self, obj, value):
        raise NotImplementedError()

    def __get__(self, obj, objtype):
        return RegisterType(self.type_name, obj)

    def copy_from_to(self, obj_src, obj_dst):
        assert obj_src.h5_type.attr_type_name == obj_dst.h5_type.attr_type_name

    def on_create(self, obj):
        obj.location.attrs[self.name] = self.type_name

    @property
    def attr_type_name(self):
        return self.obj.location.attrs.get(self.name, None)


class ChildType(Str):
    def copy_from_to(self, obj_src, obj_dst):
        assert getattr(obj_src, self.descriptor_name) == getattr(
            obj_dst, self.descriptor_name)


class H5ObjectDescriptor(Descriptor):
    def __init__(self, h5obj_type: Union[type, str], create_args=tuple(), *args, **kwargs):
        """
        if `init` is True, will be initialize after created
        """
        super().__init__(*args, **kwargs)
        self.h5obj_type = h5obj_type if isinstance(
            h5obj_type, str)else get_name(h5obj_type)
        self.create_args = create_args

    def __get__(self, obj, objtype=None):
        return get_type(self.h5obj_type)(obj.location[self.name])

    def __set__(self, obj, value: BaseHDF5Obj):
        raise NotImplementedError("Will be implement in some days")

    def copy_from_to(self, obj_src, obj_dst):
        self.__get__(obj_dst).copy_from(self.__get__(obj_src))

    def on_create(self, obj):
        sub_group = get_type(self.h5obj_type).create_at(
            obj.location, self.name, *self.create_args)
        sub_group.initialize()


class Ref_Attr(Attr):
    def __init__(self, h5obj_type: Union[type, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.h5obj_type = h5obj_type if isinstance(
            h5obj_type, str) else get_name(h5obj_type)

    def __set__(self, obj, value: BaseHDF5Obj):
        obj.location.attrs[self.name] = value.location.ref

    def __get__(self, obj, objtype):
        return get_type(self.h5obj_type)(obj.location[obj.location.attrs[self.name]])

    def copy_from_to(self, obj_src, obj_dst):
        pass
