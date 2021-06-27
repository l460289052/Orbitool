import numpy as np
from typing import List, Tuple

from ._noise import (getNoiseParams as _getNoiseParams, getNoisePeaks,
                     noiseLODFunc, denoiseWithParams)


def getNoiseParams(mass: np.ndarray, intensity: np.ndarray, quantile: float,
                   mass_dependent: bool, mass_points: np.ndarray,
                   mass_point_deltas: np.ndarray) -> Tuple[np.ndarray, List[bool], np.ndarray]:
    """
    return poly_coef, select, list[selected, params]
    """
    poly_coef, std, mass_point_rets = _getNoiseParams(mass, intensity, quantile, mass_dependent,
                                                 mass_points, mass_point_deltas)
    slt: List[bool] =np.array([ret[0] for ret in mass_point_rets])
    mass_point_params = [ret[1] for ret in mass_point_rets if ret[0]]
    mass_point_params = np.stack(mass_point_params)
    return poly_coef, std, slt, mass_point_params


def denoise(mass: np.ndarray, intensity: np.ndarray, quantile: float, n_sigma: float,
            mass_dependent: bool, mass_points: np.ndarray, mass_point_deltas: np.ndarray,
            subtract: bool) -> Tuple[np.ndarray, np.ndarray]:
    poly_coef, _, _, mass_point_params = getNoiseParams(mass, intensity, quantile, mass_dependent,
                                                     mass_points, mass_point_deltas)
    mass, intensity = denoiseWithParams(mass, intensity, poly_coef,
                                        mass_point_params, mass_points, mass_point_deltas,
                                        n_sigma, subtract)
    return mass, intensity
