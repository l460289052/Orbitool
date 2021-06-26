from pydantic import BaseModel, Field, BaseConfig


class Base(BaseModel):
    class Config(BaseConfig):
        arbitrary_types_allowed = True


class ChildTypeManager:
    def __init__(self):
        self.types = {}
        self.names = {}

    def add_type(self, name: str, typ: type):
        assert isinstance(name, str) and issubclass(typ, Base)
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
    h5_type: str = Field("base", const=True)

    def __init_subclass__(cls):
        super().__init_subclass__()
        structures.add_type(cls.__fields__["h5_type"].default, cls)


BaseStructure.__init_subclass__()


items = ChildTypeManager()


class BaseTableItem(Base):
    item_name: str = Field("BaseItem", const=True)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        items.add_type(cls.__fields__["item_name"].default, cls)
