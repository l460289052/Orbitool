from typing import Dict, Type, get_args, get_origin

from h5py import Group

from .base import Base, ChildTypeManager, TypeHandler


class StructureTypeHandler(TypeHandler):
    def write_to_h5(self, h5group: Group, key: str, value): ...
    def read_from_h5(self, h5group: Group, key: str): ...


structures = ChildTypeManager()


class BaseStructure(Base):
    h5_type = "base"

    def __init_subclass__(cls) -> None:
        cls = super().__init_subclass__()
        structures.add_type(cls.h5_type, cls)
        return cls

    @classmethod
    def get_origin(cls):
        return BaseStructure

BaseStructure.__init_subclass__()