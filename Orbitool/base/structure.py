import abc
from functools import lru_cache
from typing import Any, Callable, ClassVar, Dict, List, Tuple, Type, final, get_args, get_origin

from h5py import Group as H5Group, Dataset as H5Dataset
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

STRUCT_BASE = "_struct_base"


class BaseStructure(BaseModel):
    model_config = ConfigDict(
        # arbitrary_types_allowed=True,
        # validate_assignment=True
    )

    @classmethod
    def h5_type_handler(cls):
        return StructureTypeHandler

    def h5_write_handle(self, group: H5Group) -> List[str]:
        return [STRUCT_BASE]

    @classmethod
    def h5_read_handle(cls, group: H5Group) -> Dict[str, Any]:
        return {STRUCT_BASE: None}


class _BaseTypeHandler(abc.ABC):
    target_type: Type = None

    @final
    def __init__(self, origin, args: tuple) -> None:
        super().__init__()
        self.origin = origin
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
        h5g.attrs[key] = self.convert_to_attr(value)

    @final
    def read_from_h5(self, h5g: H5Group, key: str) -> Any:
        if key not in h5g.attrs:
            return None
        return self.convert_from_attr(h5g.attrs[key])

    @abc.abstractmethod
    def convert_to_attr(self, value): ...
    @abc.abstractmethod
    def convert_from_attr(self, value): ...


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
    def write_group_to_h5(self, group: H5Group, value): ...
    @abc.abstractmethod
    def read_group_from_h5(self, group: H5Group) -> Any: ...


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


class RowTypeHandler:
    h5_dtype = ...

    def convert_to_column(self, value: List[Any]) -> np.ndarray:
        return np.array(value, self.h5_dtype)

    def convert_from_column(self, value: np.ndarray) -> list:
        return value.tolist()


class StructureTypeHandler(GroupTypeHandler):
    target_type = BaseStructure

    def write_group_to_h5(self, group: H5Group, value: BaseStructure):
        fields = value.model_fields.copy()
        handle_fields = value.h5_write_handle(group)
        assert handle_fields.pop(
            0) == STRUCT_BASE, f"{type(value)}.struct_handle_write must append after super().struct_handle_write"
        for hf in handle_fields:
            fields.pop(hf)

        for k, field in fields.items():
            if (v := getattr(value, k, None)) is None:
                continue
            get_handler(field.annotation).write_to_h5(group, k, v)

    def read_group_from_h5(self, group) -> Any:
        cls: BaseStructure = self.origin

        fields = cls.model_fields.copy()
        # TODO: catch exceptions more exactly
        values = cls.h5_read_handle(group)
        assert STRUCT_BASE in values, f"{cls}.struct_handle_read must append after super().struct_handle_read"
        values.pop(STRUCT_BASE)

        for k in values:
            fields.pop(k)

        for k, field in fields.items():
            handler = get_handler(field.annotation)
            try:
                v = handler.read_from_h5(group, k)
            except:
                broken_entries.append('/'.join((group.name, k)))
                v = field.get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)


@ lru_cache(None) # TODO: clear after r/w
def get_handler(typ: type) -> _BaseTypeHandler:
    if hasattr(typ, "h5_type_handler"):
        Handler = getattr(typ, "h5_type_handler")()
    else:
        Handler = handlers.get(typ, None) or handlers.get(
            get_origin(typ), None)
    assert Handler is not None, f"Please register {typ}"
    return Handler(get_origin(typ) or typ, get_args(typ))


class AnnotationError(Exception):
    ...


handlers: Dict[type, Callable[[Any, tuple], _BaseTypeHandler]] = {}


broken_entries: List[str] = []
