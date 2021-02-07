from __future__ import annotations
from typing import Union, List
from collections.abc import Iterable
from datetime import datetime, timedelta
from functools import cached_property, lru_cache, partial

import h5py
import numpy as np

from .h5obj import H5Obj, ChildTypeManager
from . import descriptor as _descriptor


class DatatableItem:
    item_name = "DatatableItem"
    _child_datatable_dtypes = {}
    _child_type_manager = ChildTypeManager()

    def __init__(self, *args, from_hdf5=False, **kwargs) -> None:
        if from_hdf5:
            self.row = list(args[0])
        else:
            self.row = [None] * len(self.dtype)
            cnt = 0
            for k, v in kwargs.items():
                setattr(self, k, v)
                cnt += 1
            dtype = self.dtype
            for i, arg in enumerate(args):
                assert self.row[i] is None, "shouldn't set a kwargs which is setted in args"
                setattr(self, dtype[i][0], arg)
                cnt += 1
            assert cnt == len(self.dtype), "some dtype haven't been provided " + \
                str([self.dtype[ind][0]
                     for ind, r in enumerate(self.row) if r == None])

    def __init_subclass__(cls):
        assert cls.__base__ == DatatableItem or cls == DatatableItem, "forbid multi inherit"
        DatatableItem._child_type_manager.add_type(cls.item_name, cls)
        cls.dtype = DatatableItem._child_datatable_dtypes.get(
            cls.item_name, [])

    def __str__(self) -> str:
        return '\n'.join(
            f"{dtype[0]}: {getattr(self, dtype[0])}" for dtype in self.dtype)

    def __repr__(self) -> str:
        return '\n'.join(
            f"{dtype[0]}: {repr(getattr(self, dtype[0]))}" for dtype in self.dtype)


DatatableItem.__init_subclass__()

get_type = DatatableItem._child_type_manager.get_type
get_name = DatatableItem._child_type_manager.get_name


class Datatable(H5Obj):
    h5_type = _descriptor.RegisterType('Datatable')
    item_type = _descriptor.ChildType()

    def __init__(self, location, inited=True):
        super().__init__(location, inited)
        self.dtype: list = self.type_item_type.dtype if inited else None

    @classmethod
    def create_at(cls, location: h5py.Group, key, item_type: Union[str, type]) -> 'Datatable':
        if isinstance(item_type, type):
            item_type = get_name(item_type)
        dtype = get_type(item_type).dtype
        obj_loc = location.create_dataset(key, (0,), dtype, maxshape=(
            None,), **_descriptor.SimpleDataset.kwargs)
        obj = cls(obj_loc, False)
        obj.dtype = dtype

        for name, desc in cls._export_value_names[obj.h5_type.type_name].items():
            desc.on_create(obj)

        obj.item_type = item_type
        return obj

    @cached_property
    def type_item_type(self):
        return get_type(self.item_type)

    def __getitem__(self, s):
        t = self.type_item_type
        if isinstance(s, (slice, Iterable)):
            ds = self.location[s]
            return map(partial(t, from_hdf5=True), ds)
        return t(self.location[s], from_hdf5=True)

    def __setitem__(self, s, value: List[DatatableItem]):
        self.location[s] = [tuple(r.row) for r in value]

    def __delitem__(self, s):
        slt = np.ones(len(self.location), dtype=np.bool)
        slt[s] = False
        length = slt.sum()
        self.location[:length] = self.location[slt]
        self.location.resize((length,))

    def __iter__(self):
        return iter(self[:])  # self.__getitem__(slice(None,None,None))

    def __len__(self):
        return len(self.location)

    def get_column(self, dtype_name):
        dataDescriptor: DataDescriptor = self.type_item_type.__dict__[
            dtype_name]
        return dataDescriptor.multi_convert_from_h5(self.location[dataDescriptor.name])

    def copy_from(self, another):
        self.location.resize((len(another.location),))
        self.location[:] = another.location
        super().copy_from(another)

    @classmethod
    def descriptor(cls, child_type: Union[str, type], name=None) -> Datatable:
        return _descriptor.H5ObjectDescriptor(cls, (child_type,), name=name)

    def extend(self, rows: List[DatatableItem]):
        length = len(rows)
        self.location.resize((self.location.shape[0] + length,))
        self.location[-length:] = [tuple(r.row) for r in rows]

    def clear(self):
        self.location.resize((0,))

    def sort(self, rowIndex: Union[str, int]):
        if isinstance(rowIndex, int):
            rowIndex = self.type_item_type.dtype[rowIndex][0]
        args = self.get_column(rowIndex).argsort()
        items = self.location[:]
        items = items[args]
        self.location[:] = items


class DataDescriptor:
    dtype: np.dtype = None

    def __init__(self) -> None:
        self.name = None
        self.index = None
        self.shape = None

    def __set_name__(self, owner, name):
        assert issubclass(owner, DatatableItem)
        self.name = name
        dtypes = DatatableItem._child_datatable_dtypes
        if owner.item_name not in dtypes:
            dtype = []
            dtypes[owner.item_name] = dtype
        else:
            dtype = dtypes[owner.item_name]
        self.index = len(dtype)
        if self.shape is None:
            dtype.append((self.name, self.dtype))
        else:
            dtype.append((self.name, self.dtype, self.shape))

    def __set__(self, obj: DatatableItem, value):
        obj.row[self.index] = self.single_convert_to_h5(value)
        self.__get__.cache_clear()

    @lru_cache(4)
    def __get__(self, obj: DatatableItem, objtype):
        return self.single_convert_from_h5(obj.row[self.index])

    def single_convert_to_h5(self, value):
        return value

    def multi_convert_from_h5(self, column):
        return column

    def single_convert_from_h5(self, value):
        return value


class Bool(DataDescriptor):
    dtype = np.dtype(bool)


class Int32(DataDescriptor):
    dtype = np.dtype(np.int32)


class Int64(DataDescriptor):
    dtype = np.dtype(np.int64)


class Float32(DataDescriptor):
    dtype = np.dtype(np.float32)


class Float64(DataDescriptor):
    dtype = np.dtype(np.float64)


class str_utf8(DataDescriptor):
    dtype = h5py.string_dtype('utf-8')


class str_ascii(DataDescriptor):
    dtype = h5py.string_dtype()


class str_ascii_limit(DataDescriptor):
    def __init__(self, length, *args, **kwargs) -> None:
        self.dtype = np.dtype(f"S{length}")
        super().__init__(*args, **kwargs)

    def multi_convert_from_h5(self, column):
        return column.astype('str')

    def single_convert_from_h5(self, value):
        return value.astype('str')

    def single_convert_to_h5(self, value):
        return self.dtype.type(value)


class Datetime64s(Int64):
    def multi_convert_from_h5(self, column):
        return column.astype('M8[s]')

    def single_convert_from_h5(self, value) -> datetime:
        return value.astype('M8[s]').astype(datetime)

    def single_convert_to_h5(self, value: datetime):
        return np.datetime64(value, 's').astype(np.int64)


class Timedelta64s(Int64):
    def multi_convert_from_h5(self, column):
        return column.astype('m8[s]')

    def single_convert_from_h5(self, value):
        return value.astype('m8[s]').astype(timedelta)

    def single_convert_to_h5(self, value):
        return np.timedelta64(value, 's')


class Ndarray(DataDescriptor):
    def __init__(self, dtype, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dtype = h5py.vlen_dtype(dtype)

    def single_convert_to_h5(self, value):
        assert len(value.shape) == 1
        return super().single_convert_to_h5(value)
