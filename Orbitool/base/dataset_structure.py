from h5py import Group as H5Group, Dataset as H5Dataset

from typing import Any, List, Type, final, get_args, get_origin
import numpy as np
from numpy import testing as nptest
from pandas import read_sas
from pydantic import BaseModel

from Orbitool.base.extra_type_handlers.np_handler import NdArray
from .structure import AttrTypeHandler, BaseStructure, DatasetTypeHandler, get_handler, broken_entries
from .extra_type_handlers import np_helper

STRUCT_BASE = "_dataset_struct_base"


class BaseDatasetStructure(BaseModel):
    @classmethod
    def h5_type_handler(cls):
        return DatasetStructureTypeHandler

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        for key in self.model_fields:
            v = getattr(self, key)
            if isinstance(v, np.ndarray):
                v2 = getattr(other, key)
                if v is v2 or np.allclose(v, v2, equal_nan=True):
                    continue
                return False
            else:
                if v != getattr(other, key):
                    return False
        return True


class DatasetStructureTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.origin: Type[BaseDatasetStructure]
        fields = {}
        dataset_fields = []
        dtypes = []
        for key, field in self.origin.model_fields.items():
            annotation = field.annotation
            if get_origin(annotation) == NdArray:
                dataset_fields.append(key)
                dtypes.append(np.dtype(get_args(annotation)[0]))
            else:
                handler = get_handler(annotation)
                assert isinstance(handler, AttrTypeHandler)
                fields[key] = annotation

        self.dataset_fields = dataset_fields
        self.dtypes = dtypes
        self.annotations = fields
        self.helper = np_helper.HeteroGeneousArrayHelper(
            dataset_fields, dtypes
        )

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: BaseDatasetStructure):
        length = len(getattr(value, self.dataset_fields[0]))
        dataset = self.helper.columns_write(
            h5g, key, length, [getattr(value, df)
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

        for k, annotation in self.annotations.items():
            handler = get_handler(annotation)
            try:
                v = handler.read_from_h5(dataset, k)
            except:
                broken_entries.append('/'.join(dataset.name, f"attr:{k}"))
                v = cls.model_fields[k].get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)
