from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Union

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

    def __set_name__(self, owner, name):
        assert issubclass(
            owner, BaseHDF5Obj), "Owner class must be a subclass of `HDF5Group`"
        if self.name is None:
            self.name = name
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


class DataTable(SimpleDataset):
    def __init__(self, dtype, obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dtype = dtype
        self.obj = obj

    def __set__(self, obj, value):
        raise NotImplementedError()

    def __get__(self, obj, objtype = None):
        return DataTable(self.dtype, obj, name=self.name)

    def on_create(self, obj):
        ds = obj.location.create_dataset(
            self.name, (0,), self.dtype, maxshape=(None,), **DataTable.kwargs)

    def clear(self):
        del self.obj.location[self.name]
        self.on_create(self.obj)

    @property
    def dataset(self):
        return self.obj.location[self.name]

    def extend(self, items):
        dataset = self.dataset
        length = len(items)
        if isinstance(dataset, np.ndarray):
            dataset.resize((len(dataset)+length,),refcheck=False)
        else:
            dataset.resize((len(dataset)+length,))
        dataset[-length:] = items

    def copy_from_to(self, obj_src, obj_dst):
        dt_dst = self.__get__(obj_dst)
        dt_src = self.__get__(obj_src)
        dt_dst.clear()
        dt_dst.extend(dt_src.dataset)

class Int(Attr):
    pass


class Str(Attr):
    pass


class Float(Attr):
    pass


class Datetime(Str):
    dateFormat = r"%Y-%m-%d %H:%M:%S"
    def __get__(self, *args):
        return datetime.strptime(super().__get__(*args), self.dateFormat)

    def __set__(self, obj, value: datetime):
        super().__set__(obj, value.strftime(self.dateFormat))


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
    pass


class H5ObjectDescriptor(Descriptor):
    def __init__(self, h5obj_type: Union[type, str], init=False, init_args=None, *args, **kwargs):
        """
        if `init` is True, will be initialize after created
        """
        super().__init__(*args, **kwargs)
        self.h5obj_type = h5obj_type if isinstance(
            h5obj_type, str)else get_name(h5obj_type)
        self.init = init
        self.init_args = init_args

    def __get__(self, obj, objtype=None):
        return get_type(self.h5obj_type)(obj.location[self.name])

    def __set__(self, obj, value: BaseHDF5Obj):
        raise NotImplementedError("Will be implement in some days")

    def copy_from_to(self, obj_src, obj_dst):
        self.__get__(obj_dst).copy_from(self.__get__(obj_src))

    def on_create(self, obj):
        sub_group = get_type(self.h5obj_type).create_at(
            obj.location, self.name)
        if self.init:
            sub_group.initialize(*self.init_args)


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
