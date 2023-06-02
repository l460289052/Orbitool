from dataclasses import dataclass, fields
from typing import Callable, Dict, Generator, Generic, Iterable, Iterator, List, Mapping, Set, Tuple, Type, TypeVar, Union
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


ATTR_KEYS = "keys"


class DiskDictView(Generic[T]):
    key_type = str

    def __init__(
            self,
            group: h5py.Group,
            tmp_group: h5py.Group,
            key: str) -> None:
        self.key = key
        self.group = group
        self.tmp_group = tmp_group
        if key not in group:
            self.obj = self.init_obj()
        else:
            self.obj = group[key]
        if key not in tmp_group:
            self.tmp_obj = self.init_tmp_obj(self.obj)
        else:
            self.tmp_obj = tmp_group[key]
        self.handler: StructureTypeHandler = get_handler(BaseStructure)
        # use list for speed
        self.keys: List[str] = self.tmp_obj.attrs[ATTR_KEYS].tolist()

    def init_obj(self):
        obj = self.group.create_group(self.key)
        obj.attrs[ATTR_KEYS] = []
        return obj

    def init_tmp_obj(self, obj: h5py.Group):
        tmp_obj = self.tmp_group.create_group(self.key)
        tmp_obj.attrs[ATTR_KEYS] = obj.attrs[ATTR_KEYS].tolist()
        return tmp_obj

    # write to tmp group

    def __setitem__(self, key, value: T):
        self.handler.write_to_h5(self.tmp_obj, str(key), value)
        key = self.key_type(key)
        if key not in self.keys:
            self.keys.append(key)
            self.tmp_obj.attrs[ATTR_KEYS] = self.keys

    def __delitem__(self, key):
        s = str(key)
        if s in self.tmp_obj:
            del self.tmp_obj[s]
        self.keys.remove(self.key_type(key))
        self.tmp_obj.attrs[ATTR_KEYS] = self.keys

    def clear(self):
        self.tmp_obj.clear()
        self.keys.clear()
        self.tmp_obj.attrs[ATTR_KEYS] = self.keys

    def update(self, it: Iterable[Tuple[str, T]]):
        obj = self.tmp_obj
        handler = self.handler

        s = set(self.keys)
        keys = self.keys
        for key, v in it:
            handler.write_to_h5(obj, str(key), v)
            key = self.key_type(key)
            if key not in s:
                keys.append(key)
        self.tmp_obj.attrs[ATTR_KEYS] = keys

    # read from tmp / disk

    def __getitem__(self, key) -> T:
        key = str(key)
        return self.handler.read_from_h5(self.tmp_obj if key in self.tmp_obj else self.obj, key)

    def __len__(self):
        return len(self.keys)

    def items(self) -> Generator[Tuple[str, T], None, None]:
        obj = self.obj
        tmp_obj = self.tmp_obj
        handler = self.handler
        for key in self.keys:
            yield key, handler.read_from_h5(tmp_obj if key in tmp_obj else obj, key)

    def save_to_disk(self):
        """
            move data from tmp file to real file
            return modified
        """
        keys = set(map(str, self.keys))
        obj_keys: Set[str] = set(self.obj.keys())
        if len(self.tmp_obj) == 0 and keys == obj_keys:
            # no update
            return False
        obj = self.obj
        tmp = self.tmp_obj
        tmp_keys = set(tmp.keys())

        for to_delete in obj_keys - keys:
            del obj[to_delete]

        handler = self.handler
        for to_update in tmp_keys:
            handler.write_to_h5(
                obj, to_update,
                handler.read_from_h5(tmp, to_update))
        self.tmp_obj.clear()
        self.obj.attrs[ATTR_KEYS] = self.keys
        return True


class DiskDict(Generic[T]):
    def __init__(self, item_type: Type[T]) -> None:
        self.item_type = item_type

    def __set_name__(self, owner: BaseDiskDataProxy, name: str):
        self.name = name

    def __get__(self, ins: BaseDiskDataProxy, owner: Type[BaseDiskDataProxy]) -> DiskDictView[T]:
        return DiskDictView(ins.group, ins.tmp_group, self.name)

    def __set__(self, ins: BaseDiskDataProxy, it: Iterable[Tuple[str, T]]):
        view = DiskDictView(ins.group, ins.tmp_group, self.name)
        view.clear()
        view.update(it)


class DiskListView(DiskDictView[T]):
    key_type = int

    keys = items = update = None

    # write to tmp group

    def __setitem__(self, key: int, value: T):
        index = self.keys[key]
        return super().__setitem__(index, value)

    def __delitem__(self, key: int):
        index = self.keys[key]
        super().__delitem__(index)

    def append(self, value: T):
        if self.keys:
            index = self.keys[-1] + 1
        else:
            index = 0
        super().__setitem__(index, value)

    def extend(self, values: Iterable[T]):
        indexes = self.keys
        super().update(enumerate(values, indexes[-1] + 1 if indexes else 0))

    # read from

    def __getitem__(self, key: int) -> T:
        index = self.keys[key]
        return super().__getitem__(index)

    def __iter__(self) -> Generator[T, None, None]:
        for index in self.keys:
            yield super().__getitem__(index)


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
