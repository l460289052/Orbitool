from __future__ import annotations

import io
from typing import List, Type, TypeVar

import h5py

from ..base import get_handler
from ..base_structure import BaseStructure, StructureTypeHandler
from .h5type_handlers import Row

T = TypeVar("T")


class H5Obj:
    def __init__(self, obj) -> None:
        self._obj: h5py.Group = obj

    def write(self, path: str, value: BaseStructure):
        handler: StructureTypeHandler = get_handler(BaseStructure)
        handler.write_to_h5(self._obj, path, value)

    def read(self, path: str):
        handler: StructureTypeHandler = get_handler(BaseStructure)
        return handler.read_from_h5(self._obj, path)

    def __contains__(self, path: str) -> bool:
        return path in self._obj

    def __delitem__(self, path: str):
        del self._obj[path]

    def visit_or_create(self, path: str):
        if path in self:
            return H5Obj(self._obj[path])
        return H5Obj(self._obj.create_group(path))


class H5File(H5Obj):
    def __init__(self, path: str = None) -> None:
        if path:
            self._io = path
        else:
            self._io = io.BytesIO()
        self._file: bool = bool(path)
        self._obj: h5py.File = h5py.File(self._io, "a")

    def tmp_path(self):
        pass

    def close(self):
        self._obj.close()

    def __del__(self):
        self.close()
