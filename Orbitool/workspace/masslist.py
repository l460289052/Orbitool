from typing import List

from ..structures.base import BaseStructure, BaseRowItem, Field
from ..structures.spectrum import MassListItem


class MassListInfo(BaseStructure):
    h5_type = "mass list docker"

    rtol: float = 1e-6
    masslist: List[MassListItem] = Field(default_factory=list)
