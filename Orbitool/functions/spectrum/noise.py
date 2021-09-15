import numpy as np
from typing import List, Tuple

from ._noise import (getNoiseParams as _getNoiseParams, getNoisePeaks,
                     noiseLODFunc, denoiseWithParams)


def getNoiseParams(mass: np.ndarray, intensity: np.ndarray, quantile: float,
                   mass_dependent: bool, mass_points: np.ndarray,
                   mass_point_deltas: np.ndarray) -> Tuple[np.ndarray, List[bool], np.ndarray]:
    """
    return poly_coef, std, select, useable params
    """
    poly_coef, std, mass_point_rets = _getNoiseParams(mass, intensity, quantile, mass_dependent,
                                                      mass_points, mass_point_deltas)
    slt: List[bool] = np.array([ret[0] for ret in mass_point_rets], dtype=bool)
    mass_point_params = [ret[1] for ret in mass_point_rets if ret[0]]
    if len(mass_point_params) > 0:
        mass_point_params = np.stack(mass_point_params)
    else:
        mass_point_params = np.zeros((0, 2, 3), dtype=float)
    return poly_coef, std, slt, mass_point_params


def denoise(mass: np.ndarray, intensity: np.ndarray, quantile: float, n_sigma: float,
            mass_dependent: bool, mass_points: np.ndarray, mass_point_deltas: np.ndarray,
            subtract: bool) -> Tuple[np.ndarray, np.ndarray]:
    poly_coef, _, slt, mass_point_params = getNoiseParams(mass, intensity, quantile, mass_dependent,
                                                          mass_points, mass_point_deltas)
    mass_points = mass_points[slt]
    mass_point_deltas = mass_point_deltas[slt]
    mass, intensity = denoiseWithParams(mass, intensity, poly_coef,
                                        mass_point_params, mass_points, mass_point_deltas,
                                        n_sigma, subtract)
    return mass, intensity
