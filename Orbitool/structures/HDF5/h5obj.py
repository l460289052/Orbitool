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

    def __setitem__(self, path: str, value: BaseStructure):
        StructureConverter.write_to_h5(self._obj, path, value)

    def __getitem__(self, path: str):
        return StructureConverter.read_from_h5(self._obj, path)


class H5File(H5Obj):
    def __init__(self, path: str = None) -> None:
        if path:
            super().__init__(h5py.File(path))
        else:
            import io
            super().__init__(h5py.File(io.BytesIO(), "w"))
