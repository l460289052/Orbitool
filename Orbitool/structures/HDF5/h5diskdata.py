from dataclasses import dataclass, field, fields
from typing import Callable, Dict, Generator, Generic, Iterable, Iterator, List, Mapping, Set, Tuple, Type, TypeVar, Union
import h5py

from ..base_structure import BaseStructure, StructureTypeHandler
from ..base import get_handler

T = TypeVar('T')


@dataclass
class BaseDiskData:
    group: h5py.Group
    proxy_group: Union[h5py.Group, None] = None
    direct: bool = field(init=False)

    def iter_disk(self, callable: Callable[[Union["DiskDictDirectView", "DiskListDirectView", "DiskDictProxyView", "DiskListProxyView"]], None] = lambda x: x):
        for key, attr in type(self).__dict__.items():
            if isinstance(attr, (DiskDict, DiskList)):
                callable(getattr(self, key))

    def __post_init__(self):
        self.direct = self.proxy_group is None
        self.iter_disk()

    def save_to_disk(self):
        if not self.direct:
            self.iter_disk(lambda x: x.save_to_disk())


ATTR_KEYS = "keys"


class DiskDictDirectView(Generic[T]):
    key_type = str

    def __init__(
            self,
            group: h5py.Group,
            key: str,
            proxy=False,
            init_keys=[]) -> None:
        self.key = key
        self.group = group
        self.proxy = proxy
        if key not in group:
            self.obj = self.group.create_group(self.key)
            self.obj.attrs[ATTR_KEYS] = init_keys
        else:
            self.obj = group[key]
        self.handler: StructureTypeHandler = get_handler(BaseStructure)
        # use list for speed
        self.keys: List[str] = self.obj.attrs[ATTR_KEYS].tolist()

    def __setitem__(self, key, value: T):
        self.handler.write_to_h5(self.obj, str(key), value)
        key = self.key_type(key)
        if key not in self.keys:
            self.keys.append(key)
            self.obj.attrs[ATTR_KEYS] = self.keys

    def __delitem__(self, key):
        s = str(key)
        if s in self.obj:
            del self.obj[s]
        self.keys.remove(self.key_type(key))
        self.obj.attrs[ATTR_KEYS] = self.keys

    def clear(self):
        self.obj.clear()
        self.keys.clear()
        self.obj.attrs[ATTR_KEYS] = self.keys

    def update(self, it: Iterable[Tuple[str, T]]):
        obj = self.obj
        handler = self.handler

        s = set(self.keys)
        keys = self.keys
        for key, v in it:
            handler.write_to_h5(obj, str(key), v)
            key = self.key_type(key)
            if key not in s:
                keys.append(key)
        self.obj.attrs[ATTR_KEYS] = keys

    def __getitem__(self, key) -> T:
        assert not self.proxy
        key = str(key)
        return self.handler.read_from_h5(self.obj, key)

    def __len__(self):
        return len(self.keys)

    def items(self) -> Generator[Tuple[str, T], None, None]:
        assert not self.proxy
        obj = self.obj
        handler = self.handler
        for key in self.keys:
            yield key, handler.read_from_h5(obj, key)


class DiskDictProxyView(Generic[T]):
    key_type = str
    proxy_type = DiskDictDirectView

    def __init__(
            self,
            group: h5py.Group,
            proxy_group: h5py.Group,
            key: str) -> None:
        self.key = key
        self.group = group
        if key not in group:
            self.obj = self.group.create_group(self.key)
            self.obj.attrs[ATTR_KEYS] = []
        else:
            self.obj = group[key]
        self.direct = self.proxy_type(
            proxy_group, key, proxy=True, init_keys=self.obj.attrs[ATTR_KEYS].tolist())
        self.handler: StructureTypeHandler = get_handler(BaseStructure)
        # use list for speed
        self.keys: List[str] = self.direct.keys

    # write to tmp group

    def __setitem__(self, key, value: T):
        self.direct.__setitem__(key, value)

    def __delitem__(self, key):
        self.direct.__delitem__(key)

    def clear(self):
        self.direct.clear()

    def update(self, it: Iterable[Tuple[str, T]]):
        self.direct.update(it)

    # read from tmp / disk

    def __getitem__(self, key) -> T:
        key = str(key)
        tmp_obj = self.direct.obj
        return self.handler.read_from_h5(tmp_obj if key in tmp_obj else self.obj, key)

    def __len__(self):
        return len(self.keys)

    def items(self) -> Generator[Tuple[str, T], None, None]:
        obj = self.obj
        tmp_obj = self.direct.obj
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
        obj = self.obj
        proxy = self.direct.obj
        if len(proxy) == 0 and keys == obj_keys:
            # no update
            return False
        tmp_keys = set(proxy.keys())

        for to_delete in obj_keys - keys:
            del obj[to_delete]

        handler = self.handler
        for to_update in tmp_keys:
            handler.write_to_h5(
                obj, to_update,
                handler.read_from_h5(proxy, to_update))
        proxy.clear()
        self.obj.attrs[ATTR_KEYS] = self.keys
        return True


class DiskDict(Generic[T]):
    def __init__(self, item_type: Type[T]) -> None:
        self.item_type = item_type

    def __set_name__(self, owner: BaseDiskData, name: str):
        self.name = name

    def __get__(self, ins: BaseDiskData, owner: Type[BaseDiskData]) -> DiskDictProxyView[T]:
        if ins.direct:
            return DiskDictDirectView(ins.group, self.name)
        else:
            return DiskDictProxyView(ins.group, ins.proxy_group, self.name)

    def __set__(self, ins: BaseDiskData, it: Iterable[Tuple[str, T]]):
        if ins.direct:
            view = DiskDictDirectView(ins.group, self.name)
        else:
            view = DiskDictProxyView(ins.group, ins.proxy_group, self.name)
        view.clear()
        view.update(it)


class DiskListDirectView(DiskDictDirectView[T]):
    key_type = int

    def __setitem__(self, key: int, value: T):
        index = self.keys[key]
        return super().__setitem__(index, value)

    def __delitem__(self, key: int):
        index = self.keys[key]
        return super().__delitem__(index)

    def append(self, value: T):
        if self.keys:
            index = self.keys[-1] + 1
        else:
            index = 0
        super().__setitem__(index, value)

    def extend(self, values: Iterable[T]):
        indexes = self.keys
        super().update(enumerate(values, indexes[-1] + 1 if indexes else 0))
    
    def __getitem__(self, key: int) -> T:
        index = self.keys[key]
        return super().__getitem__(index)

    def __iter__(self) -> Generator[T, None, None]:
        assert not self.proxy
        for index in self.keys:
            yield super().__getitem__(index)


class DiskListProxyView(DiskDictProxyView[T]):
    key_type = int
    proxy_type = DiskListDirectView

    items = update = None

    def __init__(self, group: h5py.Group, proxy_group: h5py.Group, key: str) -> None:
        super().__init__(group, proxy_group, key)
        self.direct: DiskListDirectView

    # write to tmp group

    def __setitem__(self, key: int, value: T):
        self.direct.__setitem__(key, value)

    def __delitem__(self, key: int):
        self.direct.__delitem__(key)

    def append(self, value: T):
        self.direct.append(value)

    def extend(self, values: Iterable[T]):
        self.direct.extend(values)

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

    def __set_name__(self, owner: Type[BaseDiskData], name: str):
        self.name = name

    def __get__(self, ins: BaseDiskData, owner: Type[BaseDiskData]) -> DiskListProxyView[T]:
        if ins.direct:
            return DiskListDirectView(ins.group, self.name)
        else:
            return DiskListProxyView(ins.group, ins.proxy_group, self.name)

    def __set__(self, ins: BaseDiskData, values: Iterable[T]):
        if ins.direct:
            view = DiskListDirectView(ins.group, self.name)
        else:
            view = DiskListProxyView(ins.group, ins.proxy_group, self.name)
        view.clear()
        view.extend(values)
