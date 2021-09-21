from typing import TYPE_CHECKING, List
from ...structures import RowDTypeHandler
from ...structures.HDF5.h5type_handlers import StrHandler
from ._formula import Formula

if TYPE_CHECKING:
    class FormulaList(RowDTypeHandler, List[Formula]):
        pass
else:
    class FormulaList(StrHandler):
        def __call__(self, value=()):
            return list(value)

        def validate(self, value):
            return value

        def write_to_h5(self, h5group, key: str, value):
            return super().write_to_h5(h5group, key, self.convert_to_h5(value))

        def read_from_h5(self, h5group, key: str):
            return self.convert_from_h5(super().read_from_h5(h5group, key))

        def convert_to_h5(self, value):
            return ','.join(str(f) for f in value)

        def convert_from_h5(self, value: str):
            return [Formula(ss) for s in super().convert_from_h5(value).split(',') if (ss := s.strip())]
