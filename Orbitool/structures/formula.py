from . import HDF5
from functools import lru_cache
from h5py import vlen_dtype
import numpy as np

from ..utils.formula import Formula

class Descriptor(HDF5.Attr):
    @lru_cache(16)
    def __get__(self, obj, objtype=None) -> Formula:
        return Formula.from_numpy(super().__get__.__wrapped__(self, obj, objtype))

    def __set__(self, obj, value: Formula):
        return super().__set__(obj, value.to_numpy())


class DatatableDescriptor(HDF5.datatable.DataDescriptor):
    type_name = "Formula"
    dtype = vlen_dtype(np.int32)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def multi_convert_from_h5(self, column):
        return np.array([Formula.from_numpy(i.reshape(-1, 3)) for i in column], dtype=object)

    def single_convert_from_h5(self, value):
        return Formula.from_numpy(super().single_convert_from_h5(value).reshape(-1, 3))

    def single_convert_to_h5(self, value: Formula):
        return super().single_convert_to_h5(value.to_numpy().flatten())
