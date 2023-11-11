from .structure import BaseStructure, _BaseTypeHandler


class BaseRowStructure(BaseStructure):
    """
    The instance of this class will be convert to
    - a row of a dataset. If as a element of list/dict/deque/set
    - a hdf5 group. If as a field of other class

    To be convert to dataset successfully, each field's type must
    have their own `Orbitool.base.extra_type_handlers.column_handler.ColumnCellTypeHandler`
    """
    @classmethod
    def h5_rows_handler(cls) -> _BaseTypeHandler:
        pass
