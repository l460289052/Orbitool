from typing import List

from ..peakfit import MassListItem

from .base import BaseInfo


class MassListInfo(BaseInfo):
    rtol: float = 1e-6
    masslist: List[MassListItem] = []
