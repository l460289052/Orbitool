from dataclasses import dataclass, fields
from typing import Callable, Generator, Generic, Iterable, Iterator, List, Mapping, Tuple, Type, TypeVar, Union
import h5py

from ..base_structure import BaseStructure, StructureTypeHandler
from ..base import get_handler

T = TypeVar('T')


@dataclass
class BaseDiskDataProxy:
    group: h5py.Group
    tmp_group: h5py.Group

    def iter_disk(self, callable: Callable[[Union["DiskDictView", "DiskListView"]], None] = lambda x: x):
        for key, attr in type(self).__dict__.items():
            if isinstance(attr, (DiskDict, DiskList)):
                callable(getattr(self, key))

    def __post_init__(self):
        self.iter_disk()

    def save_to_disk(self):
        self.iter_disk(lambda x: x.save_to_disk())


class DiskDictView(Generic[T]):
    def __init__(
            self,
            group: h5py.Group,
            tmp_group: h5py.Group,
            key: str) -> None:
        self.key = key
        self.group = group
        self.tmp_group = tmp_group
        if key not in group:
            self.obj = group.create_group(key)
        else:
            self.obj = group[key]
        self.tmp_obj = tmp_group[key] if key in tmp_group else None
        self.handler: StructureTypeHandler = get_handler(BaseStructure)

    def copy_group(self, source: h5py.Group, target: h5py.Group):
        key = self.key
        if key in target:
            del target[key]
        source_obj = source[key]
        target_obj = target.create_group(key)
        handler = self.handler
        for key in source_obj.keys():
            value = handler.read_from_h5(source_obj, key)
            handler.write_to_h5(target_obj, key, value)

        return target_obj

    # write to tmp group

    def __setitem__(self, key, value: T):
        if self.tmp_obj is None:
            self.tmp_obj = self.copy_group(self.group, self.tmp_group)
        self.handler.write_to_h5(self.tmp_obj, str(key), value)

    def __delitem__(self, key):
        if self.tmp_obj is None:
            self.tmp_obj = self.copy_group(self.group, self.tmp_group)
        del self.tmp_obj[str(key)]

    def clear(self):
        if self.tmp_obj is None:
            self.tmp_obj = self.tmp_group.create_group(self.key)
        else:
            self.tmp_obj.clear()

    def update(self, mapping: Mapping[str, T]):
        if self.tmp_obj is None:
            self.tmp_obj = self.copy_group(self.group, self.tmp_group)
        obj = self.tmp_obj
        handler = self.handler

        for key, v in mapping.items():
            handler.write_to_h5(obj, key, v)

    # read from tmp / disk

    def __getitem__(self, key) -> T:
        obj = self.tmp_obj or self.obj
        return self.handler.read_from_h5(obj, str(key))

    def __len__(self):
        obj = self.tmp_obj or self.obj
        return len(obj)

    def keys(self):
        obj = self.tmp_obj or self.obj
        return obj.keys()

    def items(self) -> Generator[Tuple[str, T], None, None]:
        obj = self.tmp_obj or self.obj
        handler = self.handler
        for key in obj.keys():
            yield key, handler.read_from_h5(obj, key)

    def save_to_disk(self):
        """
        move data from tmp file to real file
        """
        if self.tmp_obj is None:
            # no update
            return
        self.obj = self.copy_group(self.tmp_group, self.group)
        del self.tmp_group[self.key]
        self.tmp_obj = None


class DiskDict(Generic[T]):
    def __init__(self, item_type: Type[T]) -> None:
        self.item_type = item_type

    def __set_name__(self, owner: BaseDiskDataProxy, name: str):
        self.name = name

    def __get__(self, ins: BaseDiskDataProxy, owner: Type[BaseDiskDataProxy]) -> DiskDictView[T]:
        return DiskDictView(ins.group, ins.tmp_group, self.name)

    def __set__(self, ins: BaseDiskDataProxy, mapping: Mapping[str, T]):
        view = DiskDictView(ins.group, ins.tmp_group, self.name)
        view.clear()
        view.update(mapping)


ATTR_INDEXES = "indexes"


class DiskListView(DiskDictView[T]):
    def __init__(self, group: h5py.Group, tmp_group: h5py.Group, key: str) -> None:
        super().__init__(group, tmp_group, key)
        obj = self.tmp_obj or self.obj
        if ATTR_INDEXES in obj.attrs:
            self.indexes: List[int] = obj.attrs[ATTR_INDEXES].tolist()
        else:
            self.indexes: List[int] = []

    keys = items = update = None

    # write to tmp group

    def __setitem__(self, key: int, value: T):
        index = self.indexes[key]
        return super().__setitem__(index, value)

    def __delitem__(self, key: int):
        index = self.indexes.pop(key)
        super().__delitem__(index)
        self.tmp_obj.attrs[ATTR_INDEXES] = self.indexes

    def clear(self):
        self.indexes = []
        super().clear()
        self.tmp_obj.attrs.pop(ATTR_INDEXES, None)

        if self.indexes:
            index = self.indexes[-1] + 1
        else:
            index = 0
        self.indexes.append(index)

    def append(self, value: T):
        if self.indexes:
            index = self.indexes[-1] + 1
        else:
            index = 0
        self.indexes.append(index)
        super().__setitem__(index, value)
        self.tmp_obj.attrs[ATTR_INDEXES] = self.indexes

    def extend(self, values: Iterable[T]):
        for index, value in enumerate(
                values,
                self.indexes[-1] + 1 if self.indexes else 0):
            self.indexes.append(index)
            super().__setitem__(index, value)

        self.tmp_obj.attrs[ATTR_INDEXES] = self.indexes

    # read from

    def __getitem__(self, key: int) -> T:
        index = self.indexes[key]
        return super().__getitem__(index)

    def __len__(self):
        return len(self.indexes)

    def __iter__(self) -> Generator[T, None, None]:
        obj = self.tmp_obj or self.obj
        handler = self.handler
        for index in self.indexes:
            yield handler.read_from_h5(obj, str(index))

    def save_to_disk(self):
        if self.tmp_obj is None:
            return
        super().save_to_disk()
        self.obj.attrs[ATTR_INDEXES] = self.indexes

# del DiskListView.keys
# del DiskListView.items
# del DiskListView.update


class DiskList(Generic[T]):
    def __init__(self, item_type: Type[T]) -> None:
        self.item_type = item_type

    def __set_name__(self, owner: Type[BaseDiskDataProxy], name: str):
        self.name = name

    def __get__(self, ins: BaseDiskDataProxy, owner: Type[BaseDiskDataProxy]) -> DiskListView[T]:
        return DiskListView(ins.group, ins.tmp_group, self.name)

    def __set__(self, ins: BaseDiskDataProxy, values: Iterable[T]):
        view = DiskListView(ins.group, ins.tmp_group, self.name)
        view.clear()
        view.extend(values)
