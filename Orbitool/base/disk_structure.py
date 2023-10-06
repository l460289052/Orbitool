from dataclasses import dataclass, field, fields
from typing import Callable, Dict, Generator, Generic, Iterable, Iterator, List, Mapping, Optional, Set, Tuple, Type, TypeVar, Union
import h5py

from .structure import get_handler

VT = TypeVar("VT")


@dataclass
class BaseDiskData:
    group: h5py.Group
    proxy_group: Optional[h5py.Group] = None
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


class DiskDictDirectView(Generic[VT]):
    key_type = str

    def __init__(
            self,
            value_type: Type[VT],
            group: h5py.Group,
            key: str,
            proxy=False) -> None:
        self.key = key
        self.value_type = value_type
        self.group = group
        self.proxy = proxy
        if key not in group:
            assert not proxy
            self.obj = self.group.create_group(self.key)
            self.obj.attrs[ATTR_KEYS] = []
        else:
            self.obj = group[key]
        self.handler = get_handler(value_type)
        # use list for speed, if use dict, need to be convert to list before assigned to attr
        self.keys: List[str] = self.obj.attrs[ATTR_KEYS].tolist()

    @classmethod
    def ForProxy(cls, value_type: Type[VT], group: h5py.Group, key: str, init_keys: List[str]):
        if key not in group:
            group.create_group(key).attrs[ATTR_KEYS] = init_keys
        return cls(value_type, group, key, True)

    def __setitem__(self, key: str, value: VT):
        key = str(key)
        self.handler.write_to_h5(self.obj, key, value)
        if key not in self.keys:
            self.keys.append(key)
            self.obj.attrs[ATTR_KEYS] = self.keys

    def __delitem__(self, key):
        key = str(key)
        if key in self.obj:
            del self.obj[key]
        self.keys.remove(key)
        self.obj.attrs[ATTR_KEYS] = self.keys

    def clear(self):
        self.obj.clear()
        self.keys.clear()
        self.obj.attrs[ATTR_KEYS] = self.keys

    def update(self, it: Iterable[Tuple[str, VT]]):
        obj = self.obj
        handler = self.handler

        s = set(self.keys)
        keys = self.keys
        for key, v in it:
            key = str(key)
            handler.write_to_h5(obj, key, v)
            if key not in s:
                keys.append(key)
        self.obj.attrs[ATTR_KEYS] = keys

    def __getitem__(self, key: str) -> VT:
        assert not self.proxy
        return self.handler.read_from_h5(self.obj, str(key))

    def __len__(self):
        return len(self.keys)

    def items(self) -> Generator[Tuple[str, VT], None, None]:
        assert not self.proxy
        obj = self.obj
        handler = self.handler
        for key in self.keys:
            yield key, handler.read_from_h5(obj, str(key))


class DiskDictProxyView(Generic[VT]):
    key_type = str
    proxy_type = DiskDictDirectView

    def __init__(
            self,
            value_type: VT,
            group: h5py.Group,
            proxy_group: h5py.Group,
            key: str) -> None:
        self.value_type = value_type
        self.key = key
        self.group = group
        if key not in group:
            self.obj = self.group.create_group(self.key)
            self.obj.attrs[ATTR_KEYS] = []
        else:
            self.obj = group[key]
        self.proxy = self.proxy_type.ForProxy(
            value_type, proxy_group, key, self.obj.attrs[ATTR_KEYS].tolist())
        self.handler = self.proxy.handler  # alias for proxy handler
        self.keys: List[str] = self.proxy.keys  # alias for proxy keys

    # write to tmp group
    def __setitem__(self, key: str, value: VT):
        self.proxy.__setitem__(key, value)

    def __delitem__(self, key: str):
        self.proxy.__delitem__(key)

    def clear(self):
        self.proxy.clear()

    def update(self, it: Iterable[Tuple[str, VT]]):
        self.proxy.update(it)

    # read from tmp / disk
    def __getitem__(self, key: str) -> VT:
        key = str(key)
        proxy_obj = self.proxy.obj
        return self.handler.read_from_h5(proxy_obj if key in proxy_obj else self.obj, key)

    def __len__(self):
        return len(self.keys)

    def items(self) -> Generator[Tuple[str, VT], None, None]:
        obj = self.obj
        proxy_obj = self.proxy.obj
        handler = self.handler
        for key in self.keys:
            yield key, handler.read_from_h5(proxy_obj if key in proxy_obj else obj, key)

    def save_to_disk(self):
        """
            move data from tmp file to real file
            return modified
        """
        proxy_keys = set(map(str, self.keys))
        proxy_obj = self.proxy.obj
        keys: Set[str] = set(self.obj.keys())
        obj = self.obj
        if len(proxy_obj) == 0 and proxy_keys == keys:
            # no update
            return False
        modified_keys = set(proxy_obj.keys())

        for to_delete in keys - proxy_keys:
            del obj[to_delete]

        handler = self.handler
        for key in modified_keys:
            handler.write_to_h5(
                obj, key,
                handler.read_from_h5(proxy_obj, key))
        proxy_obj.clear()  # keep the kes
        self.obj.attrs[ATTR_KEYS] = self.keys
        return True


class DiskDict(Generic[VT]):
    def __init__(self, value_type: Type[VT]) -> None:
        self.value_type = value_type

    def __set_name__(self, owner: BaseDiskData, name: str):
        self.name = name

    def __get__(self, ins: BaseDiskData, owner: Type[BaseDiskData]) -> DiskDictProxyView[VT]:
        if ins.direct:
            return DiskDictDirectView(self.value_type, ins.group, self.name)
        else:
            return DiskDictProxyView(self.value_type, ins.group, ins.proxy_group, self.name)

    def __set__(self, ins: BaseDiskData, it: Iterable[Tuple[str, VT]]):
        if ins.direct:
            view = DiskDictDirectView(self.value_type, ins.group, self.name)
        else:
            view = DiskDictProxyView(
                self.value_type, ins.group, ins.proxy_group, self.name)
        view.clear()
        view.update(it)


class DiskListDirectView(DiskDictDirectView[VT]):
    items = update = None

    def __setitem__(self, index: int, value: VT):
        key = self.keys[index]
        return super().__setitem__(key, value)

    def __delitem__(self, index: int):
        key = self.keys[index]
        return super().__delitem__(key)

    def append(self, value: VT):
        if self.keys:
            key = int(self.keys[-1]) + 1
        else:
            key = 0
        super().__setitem__(key, value)

    def extend(self, values: Iterable[VT]):
        keys = self.keys
        super().update(enumerate(values, int(keys[-1]) + 1 if keys else 0))

    def __getitem__(self, index: int) -> VT:
        key = self.keys[index]
        return super().__getitem__(key)

    def __iter__(self) -> Generator[VT, None, None]:
        assert not self.proxy
        for key in self.keys:
            yield super().__getitem__(key)


class DiskListProxyView(DiskDictProxyView[VT]):
    proxy_type = DiskListDirectView
    proxy: DiskListDirectView

    items = update = None

    # write to tmp group
    def __setitem__(self, index: int, value: VT):
        self.proxy.__setitem__(index, value)

    def __delitem__(self, index: int):
        self.proxy.__delitem__(index)

    def append(self, value: VT):
        self.proxy.append(value)

    def extend(self, values: Iterable[VT]):
        self.proxy.extend(values)

    # read from
    def __getitem__(self, index: int) -> VT:
        key = self.keys[index]
        return super().__getitem__(key)

    def __iter__(self) -> Generator[VT, None, None]:
        for key in self.keys:
            yield super().__getitem__(key)


class DiskList(Generic[VT]):
    def __init__(self, value_type: Type[VT]) -> None:
        self.value_type = value_type

    def __set_name__(self, owner: Type[BaseDiskData], name: str):
        self.name = name

    def __get__(self, ins: BaseDiskData, owner: Type[BaseDiskData]) -> DiskListProxyView[VT]:
        if ins.direct:
            return DiskListDirectView(self.value_type, ins.group, self.name)
        else:
            return DiskListProxyView(self.value_type, ins.group, ins.proxy_group, self.name)

    def __set__(self, ins: BaseDiskData, values: Iterable[VT]):
        if ins.direct:
            view = DiskListDirectView(self.value_type, ins.group, self.name)
        else:
            view = DiskListProxyView(self.value_type, ins.group, ins.proxy_group, self.name)
        view.clear()
        view.extend(values)
