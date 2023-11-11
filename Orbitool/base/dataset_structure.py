from collections import deque
from h5py import Group as H5Group, Dataset as H5Dataset

from typing import Any, List, Type, final, get_args, get_origin, Dict
import numpy as np

from Orbitool.base.extra_type_handlers.np_handler import NdArray
from .structure import MISSING, AttrTypeHandler, BaseStructure, DatasetTypeHandler, get_handler, broken_entries
from .extra_type_handlers import np_helper, Array
from .extra_type_handlers.column_handler import ColumnCellTypeHandler, ColumnHandler

STRUCT_BASE = "_dataset_struct_base"

SUPPORT_DATA = {
    NdArray, list, Array, deque, dict
}


class BaseDatasetStructure(BaseStructure):
    """
    The whole will be converted into a numpy dataset

    Example A:
        class NewStructure(BaseDatasetStructure):
            a: List[int]
            b: List[float]
            attr_a: int
            attr_b: float
    Example B:
        class NewStructure(BaseDatasetStructure):
            a: List[OtherRowType] # OtherRowType is subclass of BaseRowStructure
            attr_a: int
            attr_b: float
    Error A:
        # a and b will conflict
        class NewStructure(BaseDatasetStructure):
            a: List[OtherRowType] # OtherRowType is subclass of BaseRowStructure
            b: List[int]
            attr_a: int
            attr_b: float
    """
    @classmethod
    def h5_type_handler(cls):
        return DatasetStructureTypeHandler

def get_not_none_attr(value, attr, origin):
    ret = getattr(value, attr)
    assert ret is not None, f"{origin}.{attr} cannot be None"
    return ret

class DatasetStructureTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.origin: Type[BaseDatasetStructure]
        fields = {}
        dataset_fields = []
        handlers: Dict[str, ColumnHandler] = {}
        dtypes = []
        dataset_handler = None
        for key, field in self.origin.model_fields.items():
            annotation = field.annotation
            handler = get_handler(annotation)
            if isinstance(handler, ColumnHandler):
                dataset_fields.append(key)
                handlers[key] = handler
                shape = handler.get_cell_shape()
                if shape is None:
                    dtypes.append((key, handler.dtype))
                else:
                    dtypes.append((key, handler.dtype, shape))
            elif isinstance(handler, DatasetTypeHandler):
                # List[rows], Dict[key, values or rows]
                dataset_fields.append(key)
                dataset_handler = handler
                assert not (isinstance(annotation, type) and issubclass(
                    annotation, BaseDatasetStructure)), f"{self.origin}: cannot put a dataset {annotation} in another dataset"
            else:
                assert isinstance(
                    handler, AttrTypeHandler), f"{self.origin}.{key}"
                fields[key] = annotation

        self.dataset_fields = dataset_fields
        self.dataset_handler = dataset_handler
        self.handlers = handlers
        self.dtypes = dtypes
        self.annotations = fields
        if dataset_handler is not None:
            assert len(
                dataset_fields) == 1, f"{self.origin}: Dataset cannot exist with other lists or arrays {dataset_fields}"
        else:
            self.helper = np_helper.HeteroGeneousNdArrayHelper(dtypes)

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: BaseDatasetStructure):
        origin = self.origin
        if self.dataset_handler is None:
            length = len(get_not_none_attr(value, self.dataset_fields[0], origin))
            handlers = self.handlers
            dataset = self.helper.columns_write(
                h5g, key, length, [
                    get_not_none_attr(value, df, origin)
                    if (handler := handlers.get(df, None)) is None
                    else handler.convert_to_ndarray(get_not_none_attr(value, df, origin))
                    for df in self.dataset_fields]
            )
        else:
            dataset = self.dataset_handler.write_dataset_to_h5(
                h5g, key, get_not_none_attr(value, self.dataset_fields[0], origin))

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            if (v := getattr(value, k, None)) is None:
                continue
            handler.write_to_h5(dataset, k, v)
        return dataset

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        cls: Type[BaseDatasetStructure] = self.origin

        if self.dataset_handler is None:
            columns_iter = self.helper.columns_read(dataset)
            values = dict(zip(self.dataset_fields, columns_iter))
            for key, handler in self.handlers.items():
                values[key] = handler.convert_from_ndarray(values[key])
        else:
            key = self.dataset_fields[0]
            values = {key: self.dataset_handler.read_dataset_from_h5(dataset)}

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            try:
                v = handler.read_from_h5(dataset, k)
                if v is MISSING:
                    v = cls.model_fields[k].get_default(call_default_factory=True)
            except:
                broken_entries.append('/'.join(dataset.name, f"attr:{k}"))
                v = cls.model_fields[k].get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)
