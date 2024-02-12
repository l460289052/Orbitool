from dataclasses import dataclass, field, fields
from typing import Callable, Dict, Generator, Generic, Iterable, Iterator, List, Mapping, Optional, Set, Tuple, Type, TypeVar, Union, cast
import h5py

from .structure import MISSING, _BaseTypeHandler, get_handler


KEYS_H5_NAME = "_keys"
KT = TypeVar("KT")
VT = TypeVar("VT")


class IDiskView:
    key_handler: _BaseTypeHandler[List[str]] = get_handler(List[str])
    obj: h5py.Group
    keys: List[str]

    def clear(self): ...
    def __len__(self) -> int: ...
    def save_to_disk(self): ...

    def write_keys_to_h5(self):
        self.key_handler.write_to_h5(self.obj, KEYS_H5_NAME, self.keys)
        # self.obj.attrs[KEYS_H5_NAME] = self.keys

    def read_keys_from_h5(self):
        keys = self.key_handler.read_from_h5(self.obj, KEYS_H5_NAME)
        return [] if keys is MISSING else keys


class DiskDirectView(Generic[VT], IDiskView):
    def __init__(self, value_type: Type[VT], group: h5py.Group, key: str, proxy=False):
        self.key = key
        self.value_type = value_type
        self.group = group
        self.proxy = proxy
        if key not in group:
            assert not proxy
            self.obj = self.group.create_group(self.key)
            self.key_handler.write_to_h5(self.obj, KEYS_H5_NAME, [])
        else:
            self.obj = cast(h5py.Group, group[key])
        self.handler: _BaseTypeHandler[VT] = get_handler(value_type)  # type: ignore
        # use list for speed, if use dict, need to be convert to list before assigned to attr
        self.keys = self.read_keys_from_h5()

    @classmethod
    def for_proxy(cls, value_type: Type[VT], group: h5py.Group, key: str, init_keys: List[str]):
        if key not in group:
            cls.key_handler.write_to_h5(group.create_group(key), KEYS_H5_NAME, init_keys)
        return cls(value_type, group, key, True)

    def __setitem__(self, key: str, value: VT):
        self.handler.write_to_h5(self.obj, key, value)
        if key not in self.keys:
            self.keys.append(key)
            self.write_keys_to_h5()

    def __delitem__(self, key: str):
        if key in self.obj:
            del self.obj[key]
        self.keys.remove(key)
        self.write_keys_to_h5()

    def __getitem__(self, key: str) -> VT:
        assert not self.proxy
        return self.handler.read_from_h5(self.obj, str(key))

    def clear(self):
        self.obj.clear()
        self.keys.clear()
        self.write_keys_to_h5()

    def __len__(self):
        return len(self.keys)


class DiskProxyView(Generic[VT], IDiskView):
    proxy_type = DiskDirectView
    proxy: DiskDirectView

    def __init__(self, value_type: Type[VT], group: h5py.Group, proxy_group: h5py.Group, key: str) -> None:
        self.value_type = value_type
        self.key = key
        self.group = group
        if key not in group:
            self.obj = self.group.create_group(self.key)
            self.key_handler.write_to_h5(self.obj, KEYS_H5_NAME, [])
        else:
            self.obj = cast(h5py.Group, group[key])
        self.proxy = self.proxy_type.for_proxy(value_type, proxy_group, key, self.read_keys_from_h5())
        self.handler = self.proxy.handler  # alias for proxy handler
        self.keys: List[str] = self.proxy.keys  # alias for proxy keys

    # write to tmp group
    def __setitem__(self, key: str, value: VT):
        self.proxy.__setitem__(key, value)

    def __delitem__(self, key: str):
        self.proxy.__delitem__(key)

    def clear(self):
        self.proxy.clear()

    # read from tmp / disk
    def __getitem__(self, key: str) -> VT:
        key = str(key)
        proxy_obj = self.proxy.obj
        return self.handler.read_from_h5(proxy_obj if key in proxy_obj else self.obj, key)

    def __len__(self):
        return len(self.keys)

    def save_to_disk(self):
        """
            move data from tmp file to real file
            return modified
        """
        proxy_keys = set(self.keys)
        proxy_obj = self.proxy.obj
        keys: Set[str] = set(self.obj.keys())
        if KEYS_H5_NAME in keys:
            keys.remove(KEYS_H5_NAME)
        obj = self.obj
        if len(proxy_obj) == 0 and proxy_keys == keys:
            # no update
            return False
        modified_keys = set(proxy_obj.keys())
        # new or modified objs will be in proxy_obj. else it will be in obj
        if KEYS_H5_NAME in modified_keys:
            modified_keys.remove(KEYS_H5_NAME)

        for to_delete in keys - proxy_keys:
            del obj[to_delete]

        handler = self.handler
        for key in modified_keys:
            handler.write_to_h5(obj, key, handler.read_from_h5(proxy_obj, key))
        proxy_obj.clear()
        self.proxy.write_keys_to_h5()  # keep the keys
        self.write_keys_to_h5()
        return True


@dataclass
class BaseDiskData:
    group: h5py.Group
    proxy_group: Optional[h5py.Group] = None
    direct: bool = field(init=False)

    def iter_disk(self, call: Callable[[IDiskView], None] = lambda x: None):
        for key, attr in type(self).__dict__.items():
            if isinstance(attr, (DiskDict, DiskList)):
                call(getattr(self, key))

    def __post_init__(self):
        self.direct = self.proxy_group is None
        self.iter_disk()

    def save_to_disk(self):
        if not self.direct:
            self.iter_disk(lambda x: x.save_to_disk())


class IDiskDictView(Generic[VT], IDiskView):
    def __setitem__(self, key: str, value: VT): ...
    def __delitem__(self, key: str): ...
    def __getitem__(self, key: str) -> VT: ...
    def update(self, it: Iterable[Tuple[str, VT]]): ...
    def items(self) -> Generator[Tuple[str, VT], None, None]: ...


class DiskDictDirectView(DiskDirectView[VT], IDiskDictView[VT]):
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
        self.write_keys_to_h5()

    def items(self) -> Generator[Tuple[str, VT], None, None]:
        assert not self.proxy
        obj = self.obj
        handler = self.handler
        for key in self.keys:
            yield key, handler.read_from_h5(obj, str(key))


class DiskDictProxyView(DiskProxyView[VT], IDiskDictView[VT]):
    proxy_type = DiskDictDirectView
    proxy: DiskDictDirectView

    def update(self, it: Iterable[Tuple[str, VT]]):
        self.proxy.update(it)

    def items(self) -> Generator[Tuple[str, VT], None, None]:
        obj = self.obj
        proxy_obj = self.proxy.obj
        handler = self.handler
        for key in self.keys:
            yield key, handler.read_from_h5(proxy_obj if key in proxy_obj else obj, key)


class DiskDict(Generic[VT]):
    def __init__(self, value_type: Type[VT]) -> None:
        self.value_type = value_type
        self.name = ""

    def __set_name__(self, owner: BaseDiskData, name: str):
        self.name = name

    def __get__(self, ins: BaseDiskData, owner: Type[BaseDiskData]) -> IDiskDictView[VT]:
        if ins.direct:
            return DiskDictDirectView(self.value_type, ins.group, self.name)
        else:
            assert ins.proxy_group is not None
            return DiskDictProxyView(self.value_type, ins.group, ins.proxy_group, self.name)

    def __set__(self, ins: BaseDiskData, it: Iterable[Tuple[str, VT]]):
        if ins.direct:
            view = DiskDictDirectView(self.value_type, ins.group, self.name)
        else:
            assert ins.proxy_group is not None
            view = DiskDictProxyView(self.value_type, ins.group, ins.proxy_group, self.name)
        view.clear()
        view.update(it)


class IDiskListView(Generic[VT], IDiskView):
    def __setitem__(self, key: int, value: VT): ...
    def __delitem__(self, key: int): ...
    def __getitem__(self, key: int) -> VT: ...
    def append(self, value: VT): ...
    def extend(self, values: Iterable[VT]): ...
    def __iter__(self) -> Generator[VT, None, None]: ...


class DiskListDirectView(DiskDirectView[VT], IDiskListView[VT]):
    def __setitem__(self, index: int, value: VT):
        super().__setitem__(self.keys[index], value)

    def __delitem__(self, index: int):
        super().__delitem__(self.keys[index])

    def __getitem__(self, index: int) -> VT:
        return super().__getitem__(self.keys[index])

    def append(self, value: VT):
        if self.keys:
            key = int(self.keys[-1]) + 1
        else:
            key = 0
        super().__setitem__(str(key), value)

    def extend(self, values: Iterable[VT]):
        obj = self.obj
        handler = self.handler
        keys = self.keys
        for k, v in enumerate(values, int(keys[-1]) + 1 if keys else 0):
            k = str(k)
            handler.write_to_h5(obj, k, v)
            keys.append(k)
        self.write_keys_to_h5()

    def __iter__(self) -> Generator[VT, None, None]:
        assert not self.proxy
        for key in self.keys:
            yield super().__getitem__(key)


class DiskListProxyView(DiskProxyView[VT], IDiskListView[VT]):
    proxy_type = DiskListDirectView
    proxy: DiskListDirectView

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
        return super().__getitem__(self.keys[index])

    def __iter__(self) -> Generator[VT, None, None]:
        for key in self.keys:
            yield super().__getitem__(key)


class DiskList(Generic[VT]):
    def __init__(self, value_type: Type[VT]) -> None:
        self.value_type = value_type
        self.name: str = ""

    def __set_name__(self, owner: Type[BaseDiskData], name: str):
        self.name = name

    def __get__(self, ins: BaseDiskData, owner: Type[BaseDiskData]) -> IDiskListView[VT]:
        if ins.direct:
            return DiskListDirectView(self.value_type, ins.group, self.name)
        else:
            assert ins.proxy_group is not None
            return DiskListProxyView(self.value_type, ins.group, ins.proxy_group, self.name)

    def __set__(self, ins: BaseDiskData, values: Iterable[VT]):
        if ins.direct:
            view = DiskListDirectView(self.value_type, ins.group, self.name)
        else:
            assert ins.proxy_group is not None
            view = DiskListProxyView(self.value_type, ins.group, ins.proxy_group, self.name)
        view.clear()
        view.extend(values)
