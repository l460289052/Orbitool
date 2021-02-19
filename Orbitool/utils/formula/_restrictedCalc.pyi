from typing import List, Dict
from ._formula import Formula


class Calculator:
    def __init__(self):
        self.rtol: float = ...
        self.charge: int = ...

    def setEI(self, key: str, use: bool = True): ...
    def getElements(self) -> List[str]: ...
    def getIsotopes(self) -> List[str]: ...

    def __setitem__(self, element: str, parameters: Dict[str, float]):
        """
        dict:{
            "Min":...,
            "Max":...,
            "DBE2":...,
            "HMin":...,
            "HMax":...,
            "OMin":...,
            "OMax":...  }
        """
        ...

    def __getitem__(self, element: str) -> Dict[str, float]: ...
    def calc(self, MMin, MMax) -> None: ...
    def clear(self) -> None: ...
    def get(self, M: float) -> List[Formula]: ...
