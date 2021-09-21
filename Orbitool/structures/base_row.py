from .base import Base, ChildTypeManager, TypeHandler

row_items = ChildTypeManager()


class BaseRowItem(Base):
    item_name = "BaseRowItem"

    def __init_subclass__(cls) -> None:
        cls = super().__init_subclass__()
        row_items.add_type(cls.item_name, cls)
        return cls


class RowDTypeHandler(TypeHandler):
    def dtype(self):
        pass

    def convert_to_h5(self, value):
        return value

    def convert_from_h5(self, value):
        return value
