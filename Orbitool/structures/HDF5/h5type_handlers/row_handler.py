from typing import Tuple, Dict, Type
from functools import lru_cache
from .base import *


@lru_cache(None)
def get_dtype(item_type: BaseTableItem) -> Tuple[list, Dict[str, Type[Dtype]]]:
    dtypes = []
    converter = {}
    for key, field in item_type.__fields__.items():
        if key != "item_name":
            dtype = type_dtype.get(field.outer_type_, field.outer_type_)

            if not issubclass(dtype if isinstance(dtype, type) else type(dtype), Dtype):
                raise TypeError(
                    f'{items.get_name(item_type)} member "{key}" type "{dtype}" should be registered or as a subclass of Dtype')
            if not hasattr(dtype, "dtype"):
                raise TypeError(
                    f"Maybe you should use {dtype}[some argument] instead of {dtype}")
            if isinstance(dtype.dtype, tuple):
                dtypes.append((key, *dtype.dtype))  # name, dtype, shape
            else:
                dtypes.append((key, dtype.dtype))  # name, dtype
            converter[key] = dtype
    return dtypes, converter


class RowHandler(TypeHandler):
    @classmethod
    def write_to_h5(cls, args: tuple, h5group: Group, key: str, value):
        if key in h5group:
            del h5group[key]
        dtype, converter = get_dtype(item_type)
        dataset = h5group.create_dataset(
            key, (len(values),), dtype, compression="gzip", compression_opts=1)
        rows = [tuple(conv.convert_to_h5(getattr(value, k))
                      for k, conv in converter.items()) for value in values]

        dataset[:] = rows
        dataset.attrs["item_name"] = item_type.__fields__["item_name"].default

    @classmethod
    def read_from_h5(cls, args: tuple, h5group: Group, key: str):
        dtype, converter = get_dtype(item_type)
        dataset = h5group[key]

        rows = dataset[()]
        keys = rows.dtype.names
        rets = []
        for row in rows:
            rets.append(item_type(**{key: conv.convert_from_h5(value) for value, key in zip(
                row, keys) if (conv := converter.get(key, None)) is not None}))
        return rets
