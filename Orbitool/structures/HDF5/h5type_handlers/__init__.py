from . import list_handler, np_handler, simple_handler, structure_handler
from .array_handler import Array
from .base import BaseStructure, register_handler
from .row_handler import Row
from .simple_handler import AsciiLimit, AttrHandler
from .np_handler import NdArray

register_handler(bool, simple_handler.BoolHandler)
register_handler(int, simple_handler.IntHandler)
register_handler(str, simple_handler.StrHandler)
register_handler(float, simple_handler.FloatHandler)
register_handler(simple_handler.date, simple_handler.DateConverter)
register_handler(simple_handler.datetime, simple_handler.DatetimeConverter)

register_handler(list, list_handler.ListHandler)

register_handler(np_handler.np.ndarray, np_handler.NdArray)

register_handler(BaseStructure, structure_handler.StructureHandler)
