from .structure import BaseStructure, _BaseTypeHandler


class BaseRowStructure(BaseStructure):
    @classmethod
    def h5_rows_handler(cls) -> _BaseTypeHandler:
        pass
