from typing import List

from ..structures import BaseStructure, BaseRowItem, field, Row
from ..structures.spectrum import MassListItem


class MassListInfo(BaseStructure):
    h5_type = "mass list docker"

    rtol: float = 1e-6
    masslist: Row[MassListItem] = field(list)
