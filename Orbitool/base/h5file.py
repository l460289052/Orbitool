from __future__ import annotations

import io
from pathlib import Path
from typing import List, Literal, Optional, Type, TypeVar, cast

import h5py

from .structure import get_handler

T = TypeVar("T")


class H5Obj:
    def __init__(self, obj) -> None:
        self._obj: h5py.Group = obj

    def write(self, path: str, value: T, typ: Optional[Type[T]] = None):
        get_handler(typ or type(value)).write_to_h5(self._obj, path, value)

    def read(self, path: str, typ: Type[T]) -> T:
        return get_handler(typ).read_from_h5(self._obj, path)

    def __contains__(self, path: str) -> bool:
        return path in self._obj

    def __delitem__(self, path: str):
        del self._obj[path]

    def get_h5group(self, path: str) -> h5py.Group:
        """
        will create if not exist
        """
        if path in self._obj:
            return cast(h5py.Group, self._obj[path])
        return self._obj.create_group(path)


class H5File(H5Obj):
    _obj: h5py.File
    def __init__(self, path: str | Path | None = None, mode: Literal['a', 'r'] = 'a') -> None:
        if path:
            self._io = path
        else:
            self._io = io.BytesIO()
        self._file: bool = path is not None
        try:
            super().__init__(h5py.File(self._io, mode))
        except Exception as e:
            raise IOError(
                f"failed to open file {path}.if it's a tmp file, you can delete it and reopen the origin file") from e

    def tmp_path(self):
        pass

    def close(self):
        if hasattr(self, "_obj"):
            self._obj.close()

    def __del__(self):
        self.close()
