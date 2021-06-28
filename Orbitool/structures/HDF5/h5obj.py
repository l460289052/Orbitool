from __future__ import annotations

from typing import TypeVar, List, Type
import h5py

from ..base import BaseStructure
from .h5types import StructureConverter
from .h5datatable import TableConverter


T = TypeVar("T")


class H5Obj:
    def __init__(self, obj) -> None:
        self._obj: h5py.Group = obj

    def get_from_list(self, path: str, index: int):
        pass

    def write_table(self, path: str, item_type: Type[T], values: List[T]):
        TableConverter.write_to_h5(self._obj, path, item_type, values)

    def read_table(self, path: str, item_type: Type[T]) -> List[T]:
        return TableConverter.read_from_h5(self._obj, path, item_type)

    def write(self, path: str, value: BaseStructure):
        StructureConverter.write_to_h5(self._obj, path, value)

    def read(self, path: str):
        return StructureConverter.read_from_h5(self._obj, path)

    def __contains__(self, path: str) -> bool:
        return path in self._obj

    def visit_or_create(self, path: str):
        if path in self:
            return H5Obj(self._obj[path])
        return H5Obj(self._obj.create_group(path))


class H5File(H5Obj):
    def __init__(self, path: str = None) -> None:
        if path:
            self._obj: h5py.File = h5py.File(path)
        else:
            import io
            self._obj: h5py.File = h5py.File(io.BytesIO(), "w")

    def tmp_path(self):
        pass

    def close(self):
        self._obj.close()
        
    def __del__(self):
        self.close()
