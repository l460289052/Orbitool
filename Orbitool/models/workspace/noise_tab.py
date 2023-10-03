from typing import List
import numpy as np
from pydantic import Field

from .base import BaseInfo
from Orbitool.config import setting
from Orbitool.base import BaseRowStructure, NdArray, BaseStructure
from ..formula import Formula, FormulaType
from ..spectrum import Spectrum
from ..file import FileSpectrumInfo


class NoiseFormulaParameter(BaseRowStructure):
    formula: FormulaType
    delta: float = 5

    useable: bool = True
    selected: bool = True
    param: NdArray[float, (2, 3)] = np.zeros((2, 3), float)


def default_formula_parameter():
    return [NoiseFormulaParameter(Formula(f)) for f in setting.denoise.noise_formulas]


class NoiseGeneralSetting(BaseStructure):

    quantile: float = 0
    mass_dependent: bool = False
    n_sigma: float = 0
    subtract: float = True

    noise_formulas: List[NoiseFormulaParameter] = Field(
        default_factory=default_formula_parameter)
    params_inited: bool = False

    spectrum_dependent: bool = True

    def get_params(self, only_useable_point: bool = False):
        """
        useable params or all params
        return params, points, deltas
        """
        params, points, deltas = [], [], []
        for param in self.noise_formulas:
            if not only_useable_point or param.selected:
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
    spectrum_mz: np.ndarray = None
    spectrum_intensity: np.ndarray = None
    noise_mz: np.ndarray = None
    noise_intensity: np.ndarray = None


class NoiseTabInfo(BaseInfo):
    skip: bool = False
    current_spectrum: Spectrum = None

    general_setting: NoiseGeneralSetting = NoiseGeneralSetting()

    general_result: NoiseGeneralResult = NoiseGeneralResult()

    denoised_spectrum_infos: List[FileSpectrumInfo] = []
    to_be_calibrate: bool = True
