from collections import deque
from h5py import Group as H5Group, Dataset as H5Dataset

from typing import Any, List, Type, final, get_args, get_origin, Dict
import numpy as np

from Orbitool.base.extra_type_handlers.np_handler import NdArray
from .structure import AttrTypeHandler, BaseStructure, DatasetTypeHandler, get_handler, broken_entries
from .extra_type_handlers import np_helper, Array
from .extra_type_handlers.column_handler import ColumnCellTypeHandler, ColumnHandler

STRUCT_BASE = "_dataset_struct_base"

SUPPORT_DATA = {
    NdArray, list, Array, deque, dict
}


class BaseDatasetStructure(BaseStructure):
    @classmethod
    def h5_type_handler(cls):
        return DatasetStructureTypeHandler


class DatasetStructureTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.origin: Type[BaseDatasetStructure]
        fields = {}
        dataset_fields = []
        handlers: Dict[str, ColumnHandler] = {}
        dtypes = []
        dict_handler = None
        for key, field in self.origin.model_fields.items():
            annotation = field.annotation
            if get_origin(annotation) == dict:
                dataset_fields.append(key)
                dict_handler = get_handler(annotation)
                assert isinstance(dict_handler, DatasetTypeHandler)
                continue
            handler = get_handler(annotation)
            if isinstance(handler, ColumnHandler):
                dataset_fields.append(key)
                handlers[key] = handler
                shape = handler.get_cell_shape()
                if shape is None:
                    dtypes.append((key, handler.dtype))
                else:
                    dtypes.append((key, handler.dtype, shape))
            else:
                handler = get_handler(annotation)
                assert isinstance(handler, AttrTypeHandler)
                fields[key] = annotation

        self.dataset_fields = dataset_fields
        self.dict_handler = dict_handler
        self.handlers = handlers
        self.dtypes = dtypes
        self.annotations = fields
        if dict_handler is not None:
            assert len(
                dataset_fields) == 1, "Dict cannot exist with other lists or arrays"
        else:
            self.helper = np_helper.HeteroGeneousArrayHelper(dtypes)

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: BaseDatasetStructure):
        if self.dict_handler is None:
            length = len(getattr(value, self.dataset_fields[0]))
            handlers = self.handlers
            dataset = self.helper.columns_write(
                h5g, key, length, [
                    getattr(value, df)
                    if (handler := handlers.get(df, None)) is None
                    else handler.convert_to_array(getattr(value, df))
                    for df in self.dataset_fields]
            )
        else:
            dataset = self.dict_handler.write_dataset_to_h5(
                h5g, key, getattr(value, self.dataset_fields[0]))

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            if (v := getattr(value, k, None)) is None:
                continue
            handler.write_to_h5(dataset, k, v)
        return dataset

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        cls: Type[BaseDatasetStructure] = self.origin

        if self.dict_handler is None:
            columns_iter = self.helper.columns_read(dataset)
            values = dict(zip(self.dataset_fields, columns_iter))
            for key, handler in self.handlers.items():
                values[key] = handler.convert_from_array(values[key])
        else:
            key = self.dataset_fields[0]
            values = {key: self.dict_handler.read_dataset_from_h5(dataset)}

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            try:
                v = handler.read_from_h5(dataset, k)
            except:
                broken_entries.append('/'.join(dataset.name, f"attr:{k}"))
                v = cls.model_fields[k].get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)
