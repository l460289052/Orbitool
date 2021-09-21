from typing import Union, Dict, Type, get_origin, get_args
from functools import cached_property
from dataclasses import dataclass, fields, asdict, Field, MISSING
from functools import lru_cache
from h5py import Group


@dataclass
class Base:
    def __setattr__(self, name: str, value) -> None:
        typ = self.__dataclass_fields__[name].type

        handler, args = get_handler_args(typ)
        value = handler.validate(value, args)
        super().__setattr__(name, value)

    def __init_subclass__(cls) -> None:
        return dataclass(cls)


class TypeHandler:
    def __init__(self, args) -> None:
        if not isinstance(args, tuple):
            args = (args,)
        self.args = args

    def __class_getitem__(cls, args):
        return cls(args)

    def __call__(self, *args, **kwds):
        pass

    def __eq__(self, o: object) -> bool:
        return type(self) == type(o) and self.args == o.args

    def __hash__(self) -> int:
        return hash((type(self), self.args))


# dataclass

def get_default(field: Field):
    if field.default is not MISSING:
        return field.default
    return field.default_factory()


def field(default_factory=MISSING, default=MISSING):
    assert (default is MISSING) ^ (default_factory is MISSING)
    return Field(default, default_factory, True, True, None, True, None)

# Base Structure


class StructureTypeHandler(TypeHandler):
    @classmethod
    def validate(cls, value, args: tuple):
        return value

    @classmethod
    def write_to_h5(cls, args: tuple, h5group: Group, key: str, value): ...
    @classmethod
    def read_from_h5(cls, args: tuple, h5group: Group, key: str): ...


_type_handlers: Dict[Type, StructureTypeHandler] = {}


def register_handler(typ, handler: Type[StructureTypeHandler]):
    _type_handlers[typ] = handler


@lru_cache(None)
def get_handler_args(typ):
    if isinstance(typ, type):
        if issubclass(typ, BaseStructure):
            return _type_handlers.get(BaseStructure), ()
        if issubclass(typ, TypeHandler):
            return typ, ()
    elif isinstance(typ, TypeHandler):
        return type(typ), typ.args
    return _type_handlers.get(get_origin(typ) or typ, TypeHandler), get_args(typ)


class ChildTypeManager:
    def __init__(self):
        self.types = {}
        self.names = {}

    def add_type(self, name: str, typ: type):
        assert isinstance(name, str)
        assert name not in self.types or self.types[
            name] == typ, f"type name `{name}` repeated, `{str(typ)}` and `{str(self.types[name])}`"
        self.types[name] = typ
        self.names[typ] = name

    def get_type(self, name: str, default=None):
        return self.types.get(name, default)

    def get_name(self, typ: type, default=None):
        return self.names.get(typ, default)


structures = ChildTypeManager()


class BaseStructure(Base):
    h5_type = "Base"

    def __init_subclass__(cls) -> None:
        cls = super().__init_subclass__()
        structures.add_type(cls.h5_type, cls)
        return cls


# Base Row Item
row_items = ChildTypeManager()


class BaseRowItem(Base):
    item_name = "BaseRowItem"

    def __init_subclass__(cls) -> None:
        cls = super().__init_subclass__()
        row_items.add_type(cls.item_name, cls)
        return cls


class RowDTypeHandler(TypeHandler):
    @classmethod
    def dtype(cls, args):
        pass

    @classmethod
    def convert_to_h5(cls, args, value):
        pass

    @classmethod
    def convert_from_h5(cls, args, value):
        pass


# # Base Column Item
# col_items = ChildTypeManager()


# class BaseColumn(Base):
#     item_name = "BaseColumnItem"

#     def __init_subclass__(cls) -> None:
#         cls = super().__init_subclass__()
#         col_items.add_type(cls.item_name, cls)
#         return cls
