import abc
from functools import lru_cache
from typing import Any, Callable, ClassVar, Dict, Generic, List, Tuple, Type, TypeVar, Union, final, get_args, get_origin

from h5py import Group as H5Group, Dataset as H5Dataset
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

STRUCT_BASE = "_struct_base"


class BaseStructure(BaseModel):
    model_config = ConfigDict(
        # arbitrary_types_allowed=True,
        # validate_assignment=True
        validate_default=True
    )

    @classmethod
    def h5_type_handler(cls):
        return StructureTypeHandler

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        for key in self.model_fields:
            v = getattr(self, key)
            if isinstance(v, np.ndarray):
                v2 = getattr(other, key)
                if v is v2:
                    continue
                match v.dtype.char:
                    case 'e' | 'f' | 'd' | 'g':
                        if np.allclose(v, v2, equal_nan=True):
                            continue
                    case _:
                        if (v == v2).all():
                            continue
                return False
            else:
                if v != getattr(other, key):
                    return False
        return True


T = TypeVar("T")


class _BaseTypeHandler(Generic[T], abc.ABC):
    target_type: Type[T] = None

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
    def read_from_h5(self, h5g: H5Group, key: str) -> T:
        pass

    @abc.abstractmethod
    def write_to_h5(self, h5g: H5Group, key: str, value: T):
        pass


handlers: Dict[type, Callable[[T, tuple], _BaseTypeHandler[T]]] = {}


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
        return group

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
        return self.write_dataset_to_h5(h5g, key, value)

    @final
    def read_from_h5(self, h5g: H5Group, key: str) -> Any:
        if key not in h5g:
            return None
        return self.read_dataset_from_h5(h5g[key])

    @abc.abstractmethod
    def write_dataset_to_h5(
        self, h5g: H5Group, key: str, value) -> H5Dataset: ...

    @abc.abstractmethod
    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any: ...


class StructureTypeHandler(GroupTypeHandler):
    target_type = BaseStructure
    origin: BaseStructure

    def write_group_to_h5(self, group: H5Group, value: BaseStructure):
        for k, field in value.model_fields.items():
            if (v := getattr(value, k, None)) is None:
                continue
            get_handler(field.annotation).write_to_h5(group, k, v)

    def read_group_from_h5(self, group) -> Any:
        values = {}
        for k, field in self.origin.model_fields.items():
            handler = get_handler(field.annotation)
            try:
                v = handler.read_from_h5(group, k)
            except:
                broken_entries.append('/'.join((group.name, k)))
                v = field.get_default(call_default_factory=True)
            values[k] = v
        return self.origin(**values)


@lru_cache(None)  # TODO: clear after r/w
def get_handler(typ: Type[T]) -> _BaseTypeHandler[T]:
    if hasattr(typ, "h5_type_handler"):
        Handler = getattr(typ, "h5_type_handler")()
    else:
        Handler = handlers.get(typ, None) or handlers.get(
            get_origin(typ), None)
    assert Handler is not None, f"Please register {typ}"
    return Handler(get_origin(typ) or typ, get_args(typ))


class AnnotationError(Exception):
    ...


broken_entries: List[str] = []
