from .attr_handler import AttrHandler
from . import list_handler, np_handler, row_handler, structure_handler
from .array_handler import Array
from ...base import register_handler, BaseStructure

register_handler(bool, attr_handler.BoolHandler)
register_handler(int, attr_handler.IntHandler)
register_handler(str, attr_handler.StrHandler)
register_handler(float, attr_handler.FloatHandler)
register_handler(attr_handler.date, attr_handler.DateConverter)
register_handler(attr_handler.datetime, attr_handler.DatetimeConverter)

register_handler(list, list_handler.ListHandler)

register_handler(np_handler.np.ndarray, np_handler.NdArray)

register_handler(BaseStructure, structure_handler.StructureHandler)
