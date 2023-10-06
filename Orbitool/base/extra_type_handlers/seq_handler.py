from collections import deque
from types import GenericAlias
from typing import (Any, Iterable, List, Sequence, Tuple, Type, Union, cast,
                    get_args)

from h5py import Dataset as H5Dataset
from h5py import Group as H5Group
from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema, core_schema

from ..row_structure import BaseRowStructure
from ..structure import handlers
from .base import *
from .column_handler import ColumnCellTypeHandler, ColumnsHelper
from .column_handler import DequeTypeHandler as SimpleDequeTypeHandler
from .column_handler import ListTypeHandler as SimpleListTypeHandler
from .column_handler import SetTypeHandler as SimpleSetTypeHandler
from .column_handler import get_handler as get_column_handler
from .np_helper import get_converter


def SeqTypeHandler(origin, args):
    """
    List[int]
    List[OtherStructue]
    List[List[...]]
    Set[...]
    Deque[...]
    """
    inner_type = args[0]
    # if inner_type is List[...], it is not a type!
    if isinstance(inner_type, type) and issubclass(inner_type, BaseRowStructure):
        Handler = inner_type.h5_rows_handler()
        if Handler is not None:
            return Handler(origin, args)
        return SeqRowTypeHandler(origin, args)
    handler = get_column_handler(inner_type)
    if isinstance(handler, ColumnCellTypeHandler):
        if origin == list:
            return SimpleListTypeHandler(origin, args)
        elif origin == deque:
            return SimpleDequeTypeHandler(origin, args)
        elif origin == set:
            return SimpleSetTypeHandler(origin, args)
        else:
            assert False
    handler = get_handler(inner_type)
    assert isinstance(handler, (GroupTypeHandler, DatasetTypeHandler))
    return SeqStructureTypeHandler(origin, args)


handlers[list] = SeqTypeHandler
handlers[deque] = SeqTypeHandler
handlers[set] = SeqTypeHandler


class SeqRowTypeHandler(DatasetTypeHandler):
    origin: Union[Type[list], Type[deque], Type[set]]
    args: Tuple[Type[BaseRowStructure]]

    def __post_init__(self):
        super().__post_init__()
        vt = self.args[0]

        titles = []
        types = []
        for key, field in vt.model_fields.items():
            titles.append(key)
            types.append(field.annotation)
        self.titles = titles
        self.column_helper = ColumnsHelper(tuple(titles), tuple(types))

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: List[BaseRowStructure]):
        return self.column_helper.write_columns_to_h5(
            h5g, key, len(value), self.get_columns_from_objs(value)
        )

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        cls: Type[BaseRowStructure] = self.args[0]
        titles = self.titles
        rows = zip(*self.column_helper.read_columns_from_h5(dataset))
        return self.origin(cls(**dict(zip(titles, row))) for row in rows)

    def get_columns_from_objs(self, value: Iterable[BaseRowStructure]):
        """
        Put in a single function to gc `rows`
        """
        titles = self.titles
        if not value:
            return [()] * len(titles)
        rows = [tuple(getattr(v, t) for t in titles) for v in value]
        return list(zip(*rows))


class SeqStructureTypeHandler(GroupTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.handler = get_handler(self.args[0])

    def write_group_to_h5(self, group: H5Group, value: list):
        handler = self.handler
        for index, v in enumerate(value):
            handler.write_to_h5(group, str(index), v)

    def read_group_from_h5(self, group: H5Group) -> Any:
        handler = self.handler
        return self.origin(handler.read_from_h5(group, str(i)) for i in range(len(group)))


class AttrList(list):
    def __class_getitem__(cls, args):
        return GenericAlias(AttrList, args)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        args = get_args(source_type)
        ta = TypeAdapter(List[*args])
        return core_schema.no_info_before_validator_function(ta.validate_python, handler(Any))


class AttrSeqTypeHandler(AttrTypeHandler):
    target_type = AttrList

    def __post_init__(self):
        super().__post_init__()
        self.list_handler = SimpleListTypeHandler(list, self.args)
        self.converter = get_converter(self.list_handler.dtype)

    def convert_to_attr(self, value):
        return self.converter.convert_to_h5(self.list_handler.convert_to_array(value))

    def convert_from_attr(self, value):
        return self.list_handler.convert_from_array(self.converter.convert_from_h5(value))
