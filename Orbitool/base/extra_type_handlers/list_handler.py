from typing import Any, List, Type
from datetime import datetime
from h5py import Dataset as H5Dataset, Group as H5Group

import numpy as np

from .np_helper import PyColumnsHelper, PyListHelper

from ..row_structure import BaseRowStructure
from ..structure import handlers

from .base import *

# TODO


def ListTypeHandler(origin, args):
    inner_type = args[0]
    if issubclass(inner_type, BaseRowStructure):
        return ListRowTypeHandler(origin, args)
    handler = get_handler(inner_type)
    if isinstance(handler, RowTypeHandler):
        return ListSimpleTypeHandler(origin, args)
    assert isinstance(handler, (GroupTypeHandler, DatasetTypeHandler))
    return ListStructureTypeHandler(origin, args)


handlers[list] = ListTypeHandler


class ListRowTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        vt: BaseRowStructure = self.args[0]

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
        return [cls(**dict(zip(titles, row))) for row in rows]

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
        return self.list_helper.write_to_h5(h5g, key, value)

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        return self.list_helper.read_from_h5(dataset)

class ListStructureTypeHandler(GroupTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.handler = get_handler(self.args[0])
    
    def write_group_to_h5(self, group: H5Group, value:list):
        handler = self.handler
        for index, v in enumerate(value):
            handler.write_to_h5(group, str(index), v)
        
    def read_group_from_h5(self, group: H5Group) -> Any:
        handler = self.handler
        return [handler.read_from_h5(group[str(i)]) for i in range(len(group))]
