from array import array
from collections import deque
from h5py import Group as H5Group, Dataset as H5Dataset

from typing import Any, List, Type, final, get_args, get_origin, Dict
import numpy as np

from Orbitool.base.extra_type_handlers.np_handler import NdArray
from .structure import AttrTypeHandler, BaseStructure, DatasetTypeHandler, get_handler, broken_entries, RowTypeHandler
from .extra_type_handlers import np_helper, Array

STRUCT_BASE = "_dataset_struct_base"

SUPPORT_DATA = {
    NdArray, list, Array, deque
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
        types: Dict[str, Type] = {}
        handlers: Dict[str, RowTypeHandler] = {}
        dtypes = []
        for key, field in self.origin.model_fields.items():
            annotation = field.annotation
            if (origin := get_origin(annotation)) in SUPPORT_DATA:
                dataset_fields.append(key)
                if origin == NdArray:
                    dtypes.append(np.dtype(get_args(annotation)[0]))
                else:
                    if origin == Array:
                        handler = get_handler(annotation)
                    else:
                        handler = get_handler(get_args(annotation)[0])
                    assert isinstance(handler, RowTypeHandler)
                    types[key] = annotation
                    handlers[key] = handler
                    dtypes.append(handler.h5_dtype)
            else:
                handler = get_handler(annotation)
                assert isinstance(handler, AttrTypeHandler)
                fields[key] = annotation

        self.dataset_fields = dataset_fields
        self.types = types
        self.handlers = handlers
        self.dtypes = dtypes
        self.annotations = fields
        self.helper = np_helper.HeteroGeneousArrayHelper(
            dataset_fields, dtypes
        )

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: BaseDatasetStructure):
        length = len(getattr(value, self.dataset_fields[0]))
        handlers = self.handlers
        dataset = self.helper.columns_write(
            h5g, key, length, [
                getattr(value, df)
                if (handler := handlers.get(df, None)) is None
                else handler.convert_to_column(getattr(value, df))
                for df in self.dataset_fields]
        )

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            if (v := getattr(value, k, None)) is None:
                continue
            handler.write_to_h5(dataset, k, v)

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        cls: Type[BaseDatasetStructure] = self.origin

        columns_iter = self.helper.columns_read(dataset)
        values = dict(zip(self.dataset_fields, columns_iter))
        for key, handler in self.handlers.items():
            values[key] = recover_from_list(
                self.types[key], handler.convert_from_column(values[key]))

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            try:
                v = handler.read_from_h5(dataset, k)
            except:
                broken_entries.append('/'.join(dataset.name, f"attr:{k}"))
                v = cls.model_fields[k].get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)


def recover_from_list(annotation, value):
    origin = get_origin(annotation)
    if origin == deque:
        return deque(origin)
    return value
