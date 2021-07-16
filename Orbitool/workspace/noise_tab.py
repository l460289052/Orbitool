from typing import List, Optional

import numpy as np

from .. import config
from ..utils.formula import Formula
from ..structures.base import BaseStructure, BaseTableItem, Field
from ..structures.HDF5 import Ndarray
from ..structures.spectrum import Spectrum


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


class NoiseGeneralSetting(BaseStructure):
    h5_type = "noise general setting"

    quantile: float = 0
    mass_dependent: bool = False
    n_sigma: float = 0
    subtract: float = True

    noise_formulas: List[NoiseFormulaParameter] = Field(
        default_factory=default_formula_parameter)
    params_inited: bool = False

    spectrum_dependent: bool = True

    def get_params(self, useable: bool = False):
        """
        useable params or all params
        return params, points, deltas
        """
        params, points, deltas = [], [], []
        for param in self.noise_formulas:
            if not useable or param.selected:
                params.append(param.param)
                points.append(param.formula.mass())
                deltas.append(param.delta)
        if len(params) > 0:
            params = np.array(params)
        else:
            params = np.zeros([0, 2, 3])
        points = np.array(points)
        deltas = np.array(deltas, dtype=int)

        return params, points, deltas


class NoiseGeneralResult(BaseStructure):
    h5_type = "noise general result"

    poly_coef: np.ndarray = None
    global_noise_std: float = 0
    noise: np.ndarray = None
    LOD: np.ndarray = None


class NoiseTabInfo(BaseStructure):
    h5_type = "noise tab"

    skip: bool = False
    current_spectrum: Optional[Spectrum] = None

    general_setting: NoiseGeneralSetting = Field(
        default_factory=NoiseGeneralSetting)

    general_result: NoiseGeneralResult = Field(
        default_factory=NoiseGeneralResult)
