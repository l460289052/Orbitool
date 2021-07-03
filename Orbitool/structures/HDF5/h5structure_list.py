from typing import TypeVar, Type, Generic, List, Iterable, Generator, Any, Iterator
import h5py
from .h5obj import H5Obj
from .h5types import StructureConverter

T = TypeVar('T')


class StructureListView(Generic[T]):
    def __init__(self, h5group: h5py.Group, key: str, new=False) -> None:
        if key in h5group:
            if new:
                del self.obj[key]
            else:
                self.obj = h5group[key]
                return
        self.obj = h5group.create_group(key)

    @property
    def h5_path(self):
        return self.obj.name

    def h5_append(self, value: T):
        index = len(self.obj)
        StructureConverter.write_to_h5(self.obj, str(index), value)

    def h5_extend(self, values: Iterable[T]):
        for index, value in enumerate(values, len(self.obj)):
            StructureConverter.write_to_h5(self.obj, str(index), value)

    def __getitem__(self, index) -> T:
        if isinstance(index, Iterable):
            raise NotImplementedError()
        StructureConverter.read_from_h5(self.obj, str(index))

    def __setitem__(self, index, value: T):
        if isinstance(index, Iterable):
            raise NotImplementedError()
        StructureConverter.write_to_h5(self.obj, str(index), value)

    def __iter__(self) -> Generator[T, Any, Any]:
        for index in range(len(self.obj)):
            yield StructureConverter.read_from_h5(self.obj, str(index))


class StructureList(Generic[T]):
    def __init__(self, item_type: Type[T]):
        self.item_type = item_type

    def __set_name__(self, owner: H5Obj, name):
        self.name = name

    def __get__(self, instance: H5Obj, owner: Type[H5Obj]) -> StructureListView[T]:
        return StructureListView(instance._obj, self.name)

    def __set__(self, instance: H5Obj, value: List[T]):
        raise NotImplementedError()
