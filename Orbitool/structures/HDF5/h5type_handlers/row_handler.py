from __future__ import annotations
from typing import Tuple, Dict, Type, List, TypeVar,TYPE_CHECKING
from functools import lru_cache
from .base import *


@lru_cache(None)
def get_dtype(item_type: BaseRowItem) -> Tuple[list, Dict[str, RowDTypeHandler]]:
    dtypes = []
    handlers = {}
    for key, field in item_type.__dataclass_fields__.items():
        handler: RowDTypeHandler = get_handler(field.type)
        assert isinstance(handler, RowDTypeHandler)
        dtype = handler.dtype()

        if isinstance(dtype, tuple):
            dtypes.append((key, *dtype))  # name, dtype, shape
        else:
            dtypes.append((key, dtype))  # name, dtype
        handlers[key] = handler
    return dtypes, handlers


T = TypeVar("T")

if TYPE_CHECKING:
    class Row(StructureTypeHandler, List[T]):
        pass
else:
    class Row(StructureTypeHandler):
        def __init__(self, args) -> None:
            super().__init__(args=args)
            self.inner_type: BaseRowItem = self.args[0]

        def __call__(self):
            return []

        def write_to_h5(self, h5group: Group, key: str, value):
            if key in h5group:
                del h5group[key]
            inner_type = self.inner_type
            dtype, handlers = get_dtype(inner_type)
            dataset = h5group.create_dataset(
                key, (len(value),), dtype, compression="gzip", compression_opts=1)
            rows = [tuple(handler.convert_to_h5(getattr(v, k))
                        for k, handler in handlers.items()) for v in value]

            dataset[:] = rows
            dataset.attrs["item_name"] = BaseRowItem.item_name

        def read_from_h5(self, h5group: Group, key: str):
            inner_type = self.inner_type
            dtype, handlers = get_dtype(inner_type)
            dataset = h5group[key]

            rows = dataset[()]
            keys = rows.dtype.names
            return [inner_type(
                **{key: handler.convert_from_h5(v) for key, v in zip(keys, row)
                    if (handler := handlers.get(key, None)) is not None
                }) for row in rows]
