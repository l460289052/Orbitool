from typing import List, Optional

import numpy as np

from ... import config
from ...utils.formula import Formula
from ..base import BaseStructure, BaseTableItem, Field
from ..HDF5 import Ndarray
from ..spectrum import Spectrum


class NoiseFormulaParameter(BaseTableItem):
    item_name = "noise formula parameter"
    formula: Formula
    delta: float = 5

    useable: bool = True
    selected: bool = True
    param: Ndarray[float, (2, 3)] = Field(
        default_factory=lambda: np.zeros((2, 3), float))


def default_formula_parameter():
    return [NoiseFormulaParameter(
            formula=Formula(f)) for f in config.noise_formulas]


class NoiseTabInfo(BaseStructure):
    h5_type = "noise tab"

    current_spectrum: Optional[Spectrum] = None
    noise_formulas: List[NoiseFormulaParameter] = Field(
        default_factory=default_formula_parameter)

    n_sigma: float = 0
    poly_coef: np.ndarray = None
    global_noise_std: float = 0
    noise: np.ndarray = None
    LOD: np.ndarray = None
