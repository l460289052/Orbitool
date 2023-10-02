from collections import deque
from typing import Any, Iterable, List, Tuple, Type, Union
from datetime import datetime
from h5py import Dataset as H5Dataset, Group as H5Group

import numpy as np

from .np_helper import PyColumnsHelper, PyListHelper

from ..row_structure import BaseRowStructure
from ..structure import handlers

from .base import *


def SeqTypeHandler(origin, args):
    """
    List[int]
    List[OtherStructue]
    List[List[...]]
    """
    inner_type = args[0]
    # if inner_type is List[...], it is not a type!
    if isinstance(inner_type, type) and issubclass(inner_type, BaseRowStructure):
        return SeqRowTypeHandler(origin, args)
    handler = get_handler(inner_type)
    if isinstance(handler, RowTypeHandler):
        return ListSimpleTypeHandler(origin, args)
    assert isinstance(handler, (GroupTypeHandler, DatasetTypeHandler))
    return ListStructureTypeHandler(origin, args)


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
        self.column_helper = PyColumnsHelper(tuple(titles), tuple(types))

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: List[BaseRowStructure]):
        return self.column_helper.write_columns_to_h5(
            h5g, key, len(value), self.get_columns_from_objs(value)
        )

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        cls: Type[BaseRowStructure] = self.args[0]
        titles = self.titles
        rows = zip(*self.column_helper.read_columns_from_h5(dataset))
        return self.origin(cls(**dict(zip(titles, row))) for row in rows)

    def get_columns_from_objs(self, value: List[BaseRowStructure]):
        """
        Put in a single function to gc `rows`
        """
        titles = self.titles
        rows = [tuple(getattr(v, t) for t in titles) for v in value]
        return list(zip(*rows))


class ListSimpleTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.list_helper = PyListHelper(self.args[0])

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value):
        return self.list_helper.write_to_h5(h5g, key, value if isinstance(value, list) else list(value))

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        ret = self.list_helper.read_from_h5(dataset)
        if self.origin != list:
            ret = self.origin(ret)
        return ret


class ListStructureTypeHandler(GroupTypeHandler):
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
