import numpy as np

from .base import *


class NdArray(TypeHandler, np.ndarray):
    """
    NdArray[int]
    NdArray[int, (2, 3, -1)]
    """

    def __call__(self, *args, **kwds):
        return np.array(*args, **kwds)

    @classmethod
    def write_to_h5(cls, args, h5group: Group, key: str, value):
        if key in h5group:
            del h5group[key]
        h5group.create_dataset(
            key, data=value, compression="gzip", compression_opts=1)

    @classmethod
    def read_from_h5(cls, args, h5group: Group, key: str):
        return h5group[key][()]

    @classmethod
    def validate(cls, value, args: tuple):
        typ = args[0] if len(args) else None
        ndim = args[1] if len(args) > 1 else None

        if isinstance(value, np.ndarray):
            return value
        if typ:
            return np.array(value, typ)
        else:
            return np.array(value)
