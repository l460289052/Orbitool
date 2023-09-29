import abc
from functools import lru_cache
from typing import Any, Dict, List, Tuple, Type, final, get_args, get_origin

from h5py import Group as H5Group, Dataset as H5Dataset
from pydantic import BaseModel, ConfigDict

STRUCT_BASE = "_struct_base"


class BaseStructure(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    def h5_write_handle(self, group: H5Group) -> List[str]:
        return [STRUCT_BASE]

    @classmethod
    def h5_read_handle(cls, group: H5Group) -> Dict[str, Any]:
        return {STRUCT_BASE: None}

    @final
    def h5_write(self, h5g: H5Group, key: str):
        if key in h5g:
            del h5g[key]

        group = h5g.create_group(key)

        fields = self.model_fields.copy()
        handle_fields = self.h5_write_handle(group)
        assert handle_fields[0] == STRUCT_BASE, f"{type(self)}.struct_handle_write must append after super().struct_handle_write"
        for hf in handle_fields[1:]:
            fields.pop(hf)

        for k, field in fields.items():
            if ((value := getattr(self, k, None)) is None):
                continue
            annotation = field.annotation
            if isinstance(annotation, type) and issubclass(annotation, BaseStructure):
                value: BaseStructure
                value.h5_write(group, k)
            else:
                get_handler(annotation).write_to_h5(group, k, value)

    @final
    @classmethod
    def h5_read(cls, h5g: H5Group, key: str):
        if key not in h5g:
            return None

        group = h5g[key]

        fields = cls.model_fields.copy()
        # TODO: catch exceptions more exactly
        values = cls.h5_read_handle(h5g)
        assert STRUCT_BASE in values, f"{cls}.struct_handle_read must append after super().struct_handle_read"
        values.pop(STRUCT_BASE)

        for k in values:
            fields.pop(k)

        for k, field in fields.items():
            annotation = field.annotation
            try:
                if isinstance(annotation, type) and issubclass(annotation, BaseStructure):
                    v = annotation.h5_read(group, k)
                else:
                    v = get_handler(annotation).read_from_h5(group, k)
            except:
                broken_entries.append('/'.join((group.name, k)))
                v = field.get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)


class _BaseTypeHandler(abc.ABC):
    target_type: Type = None

    @final
    def __init__(self, args: tuple) -> None:
        super().__init__()
        self.args = args
        self.__post_init__()

    def __post_init__(self):
        pass

    def __init_subclass__(cls) -> None:
        if cls.target_type is not None:
            assert isinstance(cls.target_type, type)
            handlers[cls.target_type] = cls

    @abc.abstractmethod
    def read_from_h5(self, h5g: H5Group, key: str) -> Any:
        pass

    @abc.abstractmethod
    def write_to_h5(self, h5g: H5Group, key: str, value):
        pass


class AttrTypeHandler(_BaseTypeHandler):
    @final
    def write_to_h5(self, h5g: H5Group, key: str, value):
        if value is None:
            return
        h5g.attrs[key] = self.convert_to_h5(value)

    @final
    def read_from_h5(self, h5g: H5Group, key: str) -> Any:
        if key not in h5g.attrs:
            return None
        return self.convert_from_h5(h5g.attrs[key])

    @abc.abstractmethod
    def convert_to_h5(self, value): ...
    @abc.abstractmethod
    def convert_from_h5(self, value): ...


class GroupTypeHandler(_BaseTypeHandler):
    @final
    def write_to_h5(self, h5g: H5Group, key: str, value):
        if key in h5g:
            del h5g[key]
        group = h5g.create_group(key)
        self.write_group_to_h5(group, value)

    @final
    def read_from_h5(self, h5g: H5Group, key: str) -> Any:
        if key not in h5g:
            return None
        return self.read_group_from_h5(h5g[key])

    @abc.abstractmethod
    def write_group_to_h5(self, group, value): ...
    @abc.abstractmethod
    def read_group_from_h5(self, group) -> Any: ...


class DatasetTypeHandler(_BaseTypeHandler):
    @final
    def write_to_h5(self, h5g: H5Group, key: str, value):
        if key in h5g:
            del h5g[key]
        self.write_dataset_to_h5(h5g, key, value)

    @final
    def read_from_h5(self, h5g: H5Group, key: str) -> Any:
        if key not in h5g:
            return None
        return self.read_dataset_from_h5(h5g[key])

    @abc.abstractmethod
    def write_dataset_to_h5(self, h5g: H5Group, key: str, value): ...
    @abc.abstractmethod
    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any: ...


@lru_cache(None)
def get_handler(typ: type):
    handler = handlers.get(typ, None) or handlers.get(get_origin(typ), None)
    assert handler is not None, f"Please register {typ}"
    return handler(get_args(typ))


class AnnotationError(Exception):
    ...


handlers: Dict[type, Type[_BaseTypeHandler]] = {}


broken_entries: List[str] = []
