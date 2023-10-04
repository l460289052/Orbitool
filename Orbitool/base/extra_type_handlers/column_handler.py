from collections import deque
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import (Any, Callable, Dict, Generic, Iterable, List, Tuple, Type, TypeVar, Union, final,
                    get_args, get_origin)

import numpy as np
from h5py import Dataset as H5Dataset
from h5py import Group as H5Group

from Orbitool.base.extra_type_handlers.base import H5Group

from .base import *
from .np_helper import HeteroGeneousArrayHelper, HomogeneousArrayHelper

T = TypeVar("T")

class ColumnCellTypeHandler(Generic[T]):
    """
    will be added to handlers in 'seq_handler.py'
    and default use `list`
    """
    column_target = None
    dtype = None
    shape = None

    @final
    def __init__(self, origin: Type[T], args: tuple) -> None:
        super().__init__()
        self.origin = origin
        self.args = args
        self.__post_init__()

    def __post_init__(self): pass

    def __init_subclass__(cls) -> None:
        if cls.column_target is not None:
            assert isinstance(cls.column_target, type)
            handlers[cls.column_target] = cls

    def convert_to_column(self, value: List[T]) -> np.ndarray:
        return np.array(value, self.dtype)

    def convert_from_column(self, value: np.ndarray) -> List[T]:
        return value.tolist()


handlers: Dict[type, Callable[[T, tuple], ColumnCellTypeHandler[T]]] = {}


@lru_cache(None)
def get_handler(typ: type):
    Handler = handlers.get(typ, None) or handlers.get(get_origin(typ), None)
    return Handler and Handler(get_origin(typ) or typ, get_args(typ))


class IntTypeHandler(ColumnCellTypeHandler):
    column_target = int
    dtype = np.dtype("int64")


class FloatTypeHandler(ColumnCellTypeHandler):
    column_target = float
    dtype = np.dtype("float64")


class BoolTypeHandler(ColumnCellTypeHandler):
    column_target = bool
    dtype = np.dtype("bool")


class StrTypeHandler(ColumnCellTypeHandler):
    column_target = str
    dtype = np.dtype("U")


class DatetimeTypeHandler(ColumnCellTypeHandler):
    column_target = datetime
    dtype = np.dtype("datetime64[us]")


class DateTypeHandler(ColumnCellTypeHandler):
    column_target = date
    dtype = np.dtype("datetime64[D]")


class TimedeltaTypeHandler(ColumnCellTypeHandler):
    column_target = timedelta
    dtype = np.dtype("timedelta64[us]")


class ColumnHandler(DatasetTypeHandler):
    dtype: np.dtype = None
    def get_cell_shape(self) -> Union[Tuple[int], None]: pass
    def convert_to_array(self, value): pass
    def convert_from_array(self, value): pass


class ListTypeHandler(ColumnHandler):
    def __post_init__(self):
        super().__post_init__()
        self.column_handler = get_handler(self.args[0])
        self.dtype = self.column_handler.dtype
        self.array_helper = HomogeneousArrayHelper(
            self.column_handler.dtype)

    def get_cell_shape(self):
        return self.column_handler.shape

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value) -> H5Dataset:
        return self.array_helper.write(h5g, key, self.convert_to_array(value))

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        return self.convert_from_array(self.array_helper.read(dataset))

    def convert_to_array(self, value):
        return self.column_handler.convert_to_column(value)

    def convert_from_array(self, value):
        return self.column_handler.convert_from_column(value)


class DequeTypeHandler(ListTypeHandler):
    def convert_from_array(self, value):
        return deque(self.column_handler.convert_from_column(value))


class SetTypeHandler(ListTypeHandler):
    def convert_to_array(self, value):
        return self.column_handler.convert_to_column(list(value))

    def convert_from_array(self, value):
        return set(self.column_handler.convert_from_column(value))

# Array defined in array_handler.py


class ColumnsHelper:
    def __init__(self, titles: Tuple[str], types: tuple) -> None:
        handlers: List[ColumnCellTypeHandler] = []
        dtypes = []
        for title, typ in zip(titles, types, strict=True):
            handler = get_handler(typ)
            assert isinstance(handler, ColumnCellTypeHandler)
            handlers.append(handler)
            if handler.shape is not None:
                dtypes.append((title, handler.dtype, handler.shape))
            else:
                dtypes.append((title, handler.dtype))
        self.handlers = handlers
        self.array_helper = HeteroGeneousArrayHelper(dtypes)

    def write_columns_to_h5(self, h5g: H5Group, key: str, length: int, columns: Iterable[list]):
        h5_columns = []
        for handler, column in zip(self.handlers, columns, strict=True):
            h5_columns.append(handler.convert_to_column(column))
        return self.array_helper.columns_write(h5g, key, length, h5_columns)

    def read_columns_from_h5(self, dataset: H5Dataset):
        columns_iter = self.array_helper.columns_read(dataset)
        columns = []
        for handler, column in zip(self.handlers, columns_iter, strict=True):
            columns.append(handler.convert_from_column(column))
        return columns
