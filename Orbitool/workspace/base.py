from typing import Generic, Type, TypeVar

from ..structures.HDF5 import H5Obj

T = TypeVar("T")


class Widget(H5Obj, Generic[T]):
    def __init__(self, obj, info_class: Type[T]) -> None:
        super().__init__(obj)
        self._info_class = info_class
        self.info: T = self.read("info") if "info" in self else info_class()

    def save(self):
        self.write("info", self.info)
