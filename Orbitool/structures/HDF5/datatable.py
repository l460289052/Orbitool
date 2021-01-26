from typing import Union
from datetime import datetime, timedelta

import h5py
import numpy as np

from .h5obj import H5Obj, ChildTypeManager
from . import descriptor as _descriptor


class DatatableItem:
    name = "DatatableItem"
    _child_datatable_dtypes = {}
    _child_type_manager = ChildTypeManager()

    def __init__(self, row) -> None:
        self.row = row

    def __init_subclass__(cls):
        DatatableItem._child_type_manager.add_type(cls.name, cls)
        cls.dtype = DatatableItem._child_datatable_dtypes.get(cls.name, [])
    # need a friendly set interface

DatatableItem.__init_subclass__()

get_type = DatatableItem._child_type_manager.get_type
get_name = DatatableItem._child_type_manager.get_name


class _iter:
    def __init__(self, dt) -> None:
        self.dt = dt

    def __getitem__(self, s):
        t = get_type(self.dt.item_type)
        ds = self.dt.loc[s]
        for row in ds:
            yield t(ds)

    def __iter__(self):
        return self[:]


class Datatable(H5Obj):
    h5_type = _descriptor.RegisterType('Datatable')
    item_type = _descriptor.ChildType()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iter_range = _iter(self)

    @classmethod
    def create_at(cls, location: h5py.Group, key, item_type: Union[str, type]):
        if isinstance(item_type, type):
            item_type = get_name(item_type)
        obj_loc = location.create_dataset(key, (0,), get_type(
            item_type).dtype, maxshape=(None,), **_descriptor.SimpleDataset.kwargs)
        obj = cls(obj_loc, False)

        for name, desc in cls._export_value_names[obj.h5_type.type_name].items():
            desc.on_create(obj)

        obj.item_type = item_type
        return obj

    def __getitem__(self, dtype_name):
        dataDescriptor: DataDescriptor = get_type(
            self.item_type).__dict__[dtype_name]
        return dataDescriptor.multi_convert_from_h5(self.location[dataDescriptor.name])

    def copy_from(self, another):
        self.location.resize(len(another.location))
        self.location[:] = another.location
        super().copy_from(another)

    @classmethod
    def descriptor(cls, child_type: Union[str, type], name=None):
        return _descriptor.H5ObjectDescriptor(cls, (child_type,), name=name)


class DataDescriptor:
    dtype = None

    def __init__(self, name=None) -> None:
        self.name = name
        self.index = None
        self.shape = None

    def __set_name__(self, owner, name):
        assert issubclass(owner, DatatableItem)
        if self.name is None:
            self.name = name
        dtypes = DatatableItem._child_datatable_dtypes
        if owner.name not in dtypes:
            dtype = []
            dtypes[owner.name] = dtype
        else:
            dtype = dtypes[owner.name]
        self.index = len(dtype)
        if self.shape is None:
            dtype.append((self.name, self.dtype))
        else:
            dtype.append((self.name, self.dtype, self.shape))

    def __get__(self, obj: DatatableItem, objtype):
        return self.single_convert_from_h5(obj.row[self.index])

    def multi_convert_from_h5(self, column):
        return column

    def single_convert_from_h5(self, value):
        return value


class Int32(DataDescriptor):
    dtype = np.int32


class Int64(DataDescriptor):
    dtype = np.int64


class Float32(DataDescriptor):
    dtype = np.float32


class Float64(DataDescriptor):
    dtype = np.float64


class str_utf8(DataDescriptor):
    dtype = h5py.string_dtype('utf-8')


class str_ascii(DataDescriptor):
    dtype = h5py.string_dtype()


class str_ascii_limit(DataDescriptor):
    def __init__(self, length, *args, **kwargs) -> None:
        self.dtype = f"S{length}"
        super().__init__(*args, **kwargs)

    def multi_convert_from_h5(self, column):
        return column.astype('str')

    def single_convert_from_h5(self, value):
        return value.astype('str')


class Datatime64s(DataDescriptor):
    dtype = np.int64

    def multi_convert_from_h5(self, column):
        return column.astype('M8[s]')

    def single_convert_from_h5(self, value):
        return value.astype('M8[s]').astype(datetime)


class Timedelta64s(DataDescriptor):
    dtype = np.int64

    def multi_convert_from_h5(self, column):
        return column.astype('m8[s]')

    def single_convert_from_h5(self, value):
        return value.astype('m8[s]').astype(timedelta)


class Ndarray(DataDescriptor):
    def __init__(self, dtype, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dtype = h5py.vlen_dtype(dtype)