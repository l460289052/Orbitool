from typing import List

from ..structures import BaseStructure, BaseRowItem, field, Row
from ..models.spectrum.spectrum import MassListItem

from .base import BaseInfo

class MassListInfo(BaseInfo):
    h5_type = "mass list docker"

    rtol: float = 1e-6
    masslist: Row[MassListItem] = field(list)
