
from types import NoneType
from typing import Literal, Union
from ..structure import AnnotationError, handlers, get_handler


def UnionTypeHandler(origin, args: tuple):
    if len(args) == 2 and args[1] is NoneType:
        return get_handler(args[0])
    raise AnnotationError("Not support union type except Union[SomeType, None]")

handlers[Union] = UnionTypeHandler
