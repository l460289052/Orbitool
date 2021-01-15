from abc import ABCMeta
from datetime import datetime

import numpy as np

BaseHDF5Obj = None


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


class Attr(Descriptor):
    '''
    属性也可以考虑加入缓存机制，就是如果obj和name一样的话
    '''

    def __get__(self, obj, objtype=None):
        return obj.location.attrs.get(self.name, None)

    def __set__(self, obj, value):
        obj.location.attrs[self.name] = value


class Dataset(Descriptor):
    kwargs = dict(compression='gzip', compression_opts=1)

    def __get__(self, obj, objtype=None):
        dataset = obj.location.get(self.name, None)
        if dataset is None:
            return None
        ret = np.empty(dataset.shape, dtype=dataset.dtype)
        dataset.read_direct(ret)
        return ret

    def __set__(self, obj, value):
        if self.name in obj.location:
            del obj.location[self.name]
        obj.location.create_dataset(self.name, data=value, **Dataset.kwargs)

    # def generate_attr(self, attr_type: type, name=None):
    #     assert issubclass(attr_type, Attr)
    #     return attr_type('/'.join((self.name, name)) if name is not None else self.name+'/')


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


class H5ObjectDescriptor(Descriptor):
    def __init__(self, h5obj_type: type, name: str = None, init=False, init_args=None):
        """
        if `init` is True, will be initialize after created
        """
        super().__init__(name)
        self.h5obj_type = h5obj_type
        self.init = init
        self.init_args = init_args

    def __get__(self, obj, objtype):
        return self.h5obj_type(obj.location[self.name])

    def __set__(self, obj, value: BaseHDF5Obj):
        raise NotImplementedError("Will be implement in some days")


class Ref_Attr(Attr):
    def __init__(self, h5obj_type: type, name: str = None):
        super().__init__(name)
        self.h5obj_type = h5obj_type

    def __set__(self, obj, value: BaseHDF5Obj):
        obj.location.attrs[self.name] = value.location.ref

    def __get__(self, obj, objtype):
        return self.h5obj_type(obj.location.attrs[self.name])

    # 在拷贝的时候不要拷贝就好，能不能在每个属性这里定义拷贝的属性？感觉一直在group那里定义不太好

__all__ = [k for k, v in globals().items() if isinstance(v, type) and issubclass(
    v, (Descriptor, MainTypeHandler))]
