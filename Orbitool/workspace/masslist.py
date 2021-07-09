from typing import List

from ..structures.base import BaseStructure, BaseTableItem, Field
from ..structures.spectrum import MassListItem


class MassListInfo(BaseStructure):
    h5_type = "mass list docker"

    rtol: float = 5e-7
    masslist: List[MassListItem] = Field(default_factory=list)
