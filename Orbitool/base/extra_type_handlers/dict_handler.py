
from typing import Any, Dict, List, Tuple, Type

from h5py import Dataset as H5Dataset
from h5py import Group as H5Group

from ..row_structure import BaseRowStructure
from ..structure import get_handler, handlers
from .base import *
from .column_handler import ColumnCellTypeHandler
from .column_handler import ColumnsHelper
from .column_handler import get_handler as get_column_handler


def DictTypeHandler(origin, args):
    inner_type = args[1]
    if isinstance(inner_type, type) and issubclass(inner_type, BaseRowStructure):
        Handler = inner_type.h5_rows_handler() 
        if Handler is not None:
            return Handler(origin, args)
        return DictRowTypeHandler(origin, args)
    handler = get_column_handler(inner_type)
    if isinstance(handler, ColumnCellTypeHandler):
        return DictSimpleTypeHandler(origin, args)
    handler = get_handler(inner_type)
    assert isinstance(handler, (GroupTypeHandler, DatasetTypeHandler))
    return DictStructureTypeHandler(origin, args)


handlers[dict] = DictTypeHandler


class DictRowTypeHandler(DatasetTypeHandler):
    args: Tuple[Any, Type[BaseRowStructure]]

    def __post_init__(self):
        super().__post_init__()
        kt = self.args[0]
        vt = self.args[1]

        titles = []
        types = []
        for key, field in vt.model_fields.items():
            titles.append(key)
            annotation = field.annotation
            types.append(annotation)
        self.titles = titles
        self.column_helper = ColumnsHelper(
            ("_key_index", *titles), (kt, *types))

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: Dict[Any, BaseRowStructure]):
        return self.column_helper.write_columns_to_h5(
            h5g, key, len(value), self.get_columns_from_objs(value)
        )

    def read_dataset_from_h5(self, dataset: H5Dataset) -> List[Tuple[Any, BaseRowStructure]]:
        index, rows = self.get_rows_from_dataset(dataset)
        titles = self.titles
        cls = self.args[1]
        return {
            ind: cls(**dict(zip(titles, row))) for ind, row in zip(index, rows)
        }

    def get_columns_from_objs(self, value: Dict[Any, BaseRowStructure]):
        """
        Put in a single function to gc `rows`
        """
        titles = self.titles
        if not value:
            return [()] * len(titles)
        rows = [(k, *(getattr(v, t) for t in titles))
                for k, v in value.items()]
        return list(zip(*rows))

    def get_rows_from_dataset(self, dataset: H5Dataset):
        columns = self.column_helper.read_columns_from_h5(dataset)
        index = columns.pop(0)
        return index, list(zip(*columns))


class DictSimpleTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.column_helper = ColumnsHelper(("key", "value"), self.args)

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: Dict[Any, Any]):
        return self.column_helper.write_columns_to_h5(
            h5g, key, len(value), [list(value.keys()), list(value.values())]
        )

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        columns = self.column_helper.read_columns_from_h5(dataset)
        return dict(zip(*columns))


class DictStructureTypeHandler(GroupTypeHandler):
    def __post_init__(self):
        self.handler = get_handler(self.args[1])
        self.index_handler = get_handler(List[self.args[0]])

    def write_group_to_h5(self, group: H5Group, value: dict):
        handler = self.handler
        for index, v in enumerate(value.values()):
            handler.write_to_h5(group, str(index), v)

        self.index_handler.write_to_h5(group, "_index", list(value.keys()))

    def read_group_from_h5(self, group: H5Group) -> Any:
        keys = self.index_handler.read_from_h5(group, "_index")
        handler = self.handler
        return {key: handler.read_from_h5(group, str(index)) for index, key in enumerate(keys)}
