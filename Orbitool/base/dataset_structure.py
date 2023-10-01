from functools import lru_cache
from tokenize import group
from h5py import Group as H5Group, Dataset as H5Dataset

from typing import Any, List, Type, final, get_args
import numpy as np
from pydantic import BaseModel
from .structure import AttrTypeHandler, BaseStructure, DatasetTypeHandler, get_handler, broken_entries
from .extra_type_handlers import np_helper

STRUCT_BASE = "_dataset_struct_base"


class BaseDatasetStructure(BaseModel):
    @classmethod
    def h5_type_handler(cls):
        return DatasetStructureTypeHandler

    @classmethod
    def h5_dataset(cls) -> List[str]:
        return [STRUCT_BASE]

    @final
    @classmethod
    def h5_dtypes(cls) -> List[np.ndarray]:
        dataset_fields = cls.h5_dataset()
        dataset_fields.pop(0)
        dtypes: List[np.dtype] = []
        fields = cls.model_fields
        for df in dataset_fields:
            dtypes.append(np.dtype(get_args(fields[df].annotation)[0]))
        return dtypes


class DatasetStructureTypeHandler(DatasetTypeHandler):
    def __post_init__(self):
        super().__post_init__()
        self.origin: Type[BaseDatasetStructure]
        fields = self.origin.model_fields.copy()
        dataset_fields = self.origin.h5_dataset()
        assert dataset_fields.pop(
            0) == STRUCT_BASE, f"{self.origin}.h5_dataset must append after super's method"
        for df in dataset_fields:
            fields.pop(df)

        self.dataset_fields = dataset_fields
        self.fields = fields
        self.helper = np_helper.HeteroGeneousArrayHelper(
            dataset_fields, self.origin.h5_dtypes()
        )

    def write_dataset_to_h5(self, h5g: H5Group, key: str, value: BaseDatasetStructure):
        length = len(getattr(value, self.dataset_fields[0]))
        dataset = self.helper.columns_write(
            h5g, key, length, [getattr(value, df) for df in self.dataset_fields]
        )

        for k, field in self.fields.items():
            annotation = field.annotation
            handler = get_handler(annotation)
            assert isinstance(handler, AttrTypeHandler)
            if (v := getattr(self, k, None)) is None:
                continue
            handler.write_to_h5(dataset, k, v)

    def read_dataset_from_h5(self, dataset: H5Dataset) -> Any:
        cls: Type[BaseDatasetStructure] = self.origin
        fields = cls.model_fields.copy()
        dataset_fields = cls.h5_dataset()
        assert dataset_fields.pop(
            0) == STRUCT_BASE, f"{cls}.h5_dataset must append after super's method"
        for df in dataset_fields:
            fields.pop(df)

        columns_iter = self.helper.columns_read(dataset)
        values = dict(zip(dataset_fields, columns_iter))

        for k, field in fields.items():
            handler = get_handler(field.annotation)
            assert isinstance(handler, AttrTypeHandler)
            try:
                v = handler.read_from_h5(dataset, k)
            except:
                broken_entries.append('/'.join(dataset.name, f"attr:{k}"))
                v = field.get_default(call_default_factory=True)
            values[k] = v
        return cls(**values)
