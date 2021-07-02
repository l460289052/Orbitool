from . import HDF5
from .converters import register, convert, _BaseConverter, ConvertVersionCheckError, _converter
from .file import PathList

from . import h5converters

HDF5.register_converter(h5converters.Formula, h5converters.FormulaConverter)
HDF5.register_datatable_converter(
    h5converters.Formula, h5converters.FormulaDatatableConverter)

HDF5.register_converter(h5converters.RestrictedCalc,
                        h5converters.RestrictedCalcConverter)
HDF5.register_converter(h5converters.ForceCalc,
                        h5converters.ForceCalcConverter)
