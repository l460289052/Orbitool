from array import array
from Orbitool.base import Array
from .base import BaseInfo


class SpectraListInfo(BaseInfo):
    shown_indexes: Array('i') =  array('i')
