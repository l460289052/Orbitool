import abc
from collections import deque
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import (Any, Callable, Dict, Generic, Iterable, List, Optional, Tuple, Type, TypeVar, Union, final,
                    get_args, get_origin)

import numpy as np
from h5py import Dataset as H5Dataset
from h5py import Group as H5Group

from Orbitool.base.extra_type_handlers.base import H5Group

from .base import *
from .np_helper import HeteroGeneousNdArrayHelper, HomogeneousNdArrayHelper

T = TypeVar("T")


class ColumnCellTypeHandler(Generic[T]):
    """
    used by
    - ColumnsHelper to help convert a List[SomeRow] of SomeType.some_field to dataset.
    - ColumnHandler to help convert a list to a column of dataset.
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

    def convert_to_npcolumn(self, value: List[T]) -> np.ndarray:
        return np.array(value, self.dtype)

    def convert_from_npcolumn(self, value: np.ndarray) -> List[T]:
        return value.tolist()


handlers: Dict[type, Callable[[T, tuple], ColumnCellTypeHandler[T]]] = {}


@lru_cache(None)
def get_handler(typ: Type[T]) -> ColumnCellTypeHandler[T]:
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


class BytesTypeHandler(ColumnCellTypeHandler):
    column_target = bytes
    dtype = np.dtype("S")


class DatetimeTypeHandler(ColumnCellTypeHandler):
    column_target = datetime
    dtype = np.dtype("datetime64[us]")


class DateTypeHandler(ColumnCellTypeHandler):
    column_target = date
    dtype = np.dtype("datetime64[D]")


class TimedeltaTypeHandler(ColumnCellTypeHandler):
    column_target = timedelta
    dtype = np.dtype("timedelta64[us]")


class ColumnHandler(DatasetTypeHandler, abc.ABC):
    """
    used to
    - convert a list to a column of dataset.
    """
    dtype: np.dtype = None
    def get_cell_shape(self) -> Union[Tuple[int], None]:
        """
        get the shape of the list element
        - return None. The dtype will be (name, type).
        - return shape. The dtype will be (name, type, shape), like ("data", np.int32, (2, 3))
        """
        pass
    def convert_to_ndarray(self, value): pass
    def convert_from_ndarray(self, value): pass


class ListTypeHandler(ColumnHandler):
    def __post_init__(self):
        super().__post_init__()
        self.column_handler = get_handler(self.args[0])
        self.dtype = self.column_handler.dtype
        self.array_helper = HomogeneousNdArrayHelper(
            self.column_handler.dtype)

    def get_cell_shape(self):
        return self.column_handler.shape

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value) -> H5Dataset:
        return self.array_helper.write(h5g, key, self.convert_to_ndarray(value))

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        return self.convert_from_ndarray(self.array_helper.read(dataset))

    def convert_to_ndarray(self, value):
        return self.column_handler.convert_to_npcolumn(value)

    def convert_from_ndarray(self, value):
        return self.column_handler.convert_from_npcolumn(value)


class DequeTypeHandler(ListTypeHandler):
    def convert_from_ndarray(self, value):
        return deque(self.column_handler.convert_from_npcolumn(value))


class SetTypeHandler(ListTypeHandler):
    def convert_to_ndarray(self, value):
        return self.column_handler.convert_to_npcolumn(list(value))

    def convert_from_ndarray(self, value):
        return set(self.column_handler.convert_from_npcolumn(value))

# Array defined in array_handler.py


class ColumnsHelper:
    """
    used by
    - SeqHandler/DictHandler to help write columns to h5 and vice versa
    """
    def __init__(self, titles: Tuple[str], types: tuple, default_factories: Optional[Tuple[Union[Callable, None]]] = None) -> None:
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
        self.titles = titles
        self.handlers = handlers
        self.array_helper = HeteroGeneousNdArrayHelper(dtypes)
        self.default_factories = default_factories or (None,) * len(titles)

    def write_columns_to_h5(self, h5g: H5Group, key: str, length: int, columns: Iterable[list]):
        h5_columns = []
        for handler, column in zip(self.handlers, columns, strict=True):
            h5_columns.append(handler.convert_to_npcolumn(column))
        return self.array_helper.columns_write(h5g, key, length, h5_columns)

    def read_columns_from_h5(self, dataset: H5Dataset):
        length = len(dataset)
        columns_iter = self.array_helper.columns_read(dataset)
        columns = []
        for index, (handler, column) in enumerate(zip(self.handlers, columns_iter, strict=True)):
            if column is not None:
                columns.append(handler.convert_from_npcolumn(column))
            else:
                factory = self.default_factories[index]
                assert factory is not None, f"field {self.titles[index]} needs default value, because hdf5 file doesn't have this field"
                values = [factory(call_default_factory=True) for _ in range(length)]
                columns.append(values)
        return columns
