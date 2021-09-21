import math
from typing import TYPE_CHECKING

import numpy as np
from h5py import vlen_dtype

from .base import *

if TYPE_CHECKING:
    class NdArray(StructureTypeHandler, RowDTypeHandler, np.ndarray):
        """
        NdArray[int]
        NdArray[int, 100]
        NdArray[..., (2, 3, -1)]
        NdArray[int, (2, 3, -1)]
        """
        pass

else:
    class NdArray(StructureTypeHandler, RowDTypeHandler):
        def __init__(self, args) -> None:
            super().__init__(args)
            self.typ = np.dtype(args[0]) if len(args) else ...
            shape = args[1] if len(args) > 1 else ...
            resize = False
            if shape is not ...:
                if isinstance(shape, int):
                    shape = (shape,)
                for dim in shape:
                    if dim == -1:
                        assert not resize
                        resize = True
            else:
                resize = True
            self.shape = shape
            if resize:
                self._dtype = vlen_dtype(self.typ)
            else:
                self._dtype = (self.typ, math.prod(shape))

        def __call__(self, *args, **kwds):
            return np.array(*args, **kwds)

        def validate(self, value):
            typ = self.typ

            if isinstance(value, np.ndarray):
                return value
            if typ:
                return np.array(value, typ)
            else:
                return np.array(value)

        def write_to_h5(self, h5group: Group, key: str, value):
            if key in h5group:
                del h5group[key]
            h5group.create_dataset(
                key, data=value, compression="gzip", compression_opts=1)

        def read_from_h5(self, h5group: Group, key: str):
            return h5group[key][()]

        def dtype(self):
            return self._dtype

        def convert_to_h5(self, value):
            return value.reshape(-1)

        def convert_from_h5(self, value):
            if self.shape is not ...:
                return value.reshape(*self.shape)
            else:
                return value