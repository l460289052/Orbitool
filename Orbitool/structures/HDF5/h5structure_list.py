from typing import (Any, Generator, Generic, Iterable, Iterator, List, Type,
                    TypeVar)

import h5py

from ..base import get_handler_args, BaseStructure
from .h5obj import H5Obj


T = TypeVar('T')


class StructureListView(Generic[T]):
    def __init__(self, h5group: h5py.Group, key: str, new=False) -> None:
        if key in h5group:
            if new:
                del h5group[key]
            else:
                self.obj = h5group[key]
                return
        self.obj = h5group.create_group(key)

    @property
    def h5_path(self):
        return self.obj.name

    def h5_append(self, value: T):
        index = len(self.obj)
        handler, args = get_handler_args(BaseStructure)
        handler.write_to_h5(args, self.obj, str(index), value)

    def h5_extend(self, values: Iterable[T]):
        handler, args = get_handler_args(BaseStructure)
        for index, value in enumerate(values, len(self.obj)):
            handler.write_to_h5(args, self.obj, str(index), value)

    def __getitem__(self, index) -> T:
        if isinstance(index, Iterable):
            raise NotImplementedError()
        handler, args = get_handler_args(BaseStructure)
        return handler.read_from_h5(args, self.obj, str(index))

    def __setitem__(self, index, value: T):
        if isinstance(index, Iterable):
            raise NotImplementedError()
        handler, args = get_handler_args(BaseStructure)
        handler.write_to_h5(args, self.obj, str(index), value)

    def __iter__(self) -> Generator[T, Any, Any]:
        handler, args = get_handler_args(BaseStructure)
        for index in range(len(self.obj)):
            yield handler.read_from_h5(args, self.obj, str(index))

    def __len__(self):
        return len(self.obj)


class StructureList(Generic[T]):
    def __init__(self, item_type: Type[T]):
        self.item_type = item_type

    def __set_name__(self, owner: H5Obj, name):
        self.name = name

    def __get__(self, instance: H5Obj, owner: Type[H5Obj]) -> StructureListView[T]:
        return StructureListView(instance._obj, self.name)

    def __set__(self, instance: H5Obj, value: List[T]):
        raise NotImplementedError()
