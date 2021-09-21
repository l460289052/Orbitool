from .attr_converter import AttrHandler
from . import list_converter, np_converter, row_converter, structure_converter
from .array_converter import Array
from ...base import register_handler, BaseStructure

register_handler(bool, attr_converter.BoolHandler)
register_handler(int, attr_converter.IntHandler)
register_handler(str, attr_converter.StrHandler)
register_handler(float, attr_converter.FloatHandler)
register_handler(attr_converter.date, attr_converter.DateConverter)
register_handler(attr_converter.datetime, attr_converter.DatetimeConverter)

register_handler(list, list_converter.ListHandler)

register_handler(np_converter.np.ndarray, np_converter.NdArray)

register_handler(BaseStructure, structure_converter.StructureHandler)
