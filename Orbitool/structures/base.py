from typing import Union, Dict, Type, get_origin, get_args
from functools import cached_property
from dataclasses import dataclass, fields, asdict, Field, MISSING
from functools import lru_cache
from h5py import Group


@dataclass
class Base:
    def __setattr__(self, name: str, value) -> None:
        typ = self.__dataclass_fields__[name].type

        handler = get_handler(typ)
        value = handler.validate(value)
        super().__setattr__(name, value)

    def __init_subclass__(cls) -> None:
        return dataclass(cls)

    @classmethod
    def get_origin(cls):
        pass


class TypeHandler:
    def __init__(self, args=()) -> None:
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

    def validate(self, value):
        return value


_type_handlers: Dict[Type, TypeHandler] = {}


def register_handler(typ, handler: Type[TypeHandler]):
    _type_handlers[typ] = handler


@lru_cache(None)
def get_handler(typ) -> TypeHandler:
    if isinstance(typ, type):
        if issubclass(typ, Base):
            return _type_handlers.get(typ.get_origin())()
        if issubclass(typ, TypeHandler):
            return typ()
    elif isinstance(typ, TypeHandler):
        return typ
    return _type_handlers.get(get_origin(typ) or typ, TypeHandler)(get_args(typ))


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


def get_default(field: Field):
    if field.default is not MISSING:
        return field.default
    if field.default_factory is not MISSING:
        return field.default_factory()
    return field.type()


def field(default_factory=MISSING, default=MISSING):
    assert (default is MISSING) ^ (default_factory is MISSING)
    return Field(default, default_factory, True, True, None, True, None)


# # Base Column Item
# col_items = ChildTypeManager()


# class BaseColumn(Base):
#     item_name = "BaseColumnItem"

#     def __init_subclass__(cls) -> None:
#         cls = super().__init_subclass__()
#         col_items.add_type(cls.item_name, cls)
#         return cls
