from typing import Union
import numpy as np


def maxFitNum(peak_num: int) -> int: ...


def func(mz: Union[float, np.ndarray], a: float, mu: float,
         sigma: float) -> Union[float, np.ndarray]: ...


def mergePeaksParam(param1: tuple, param2: tuple) -> tuple: ...
