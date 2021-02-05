import numpy as np
from typing import List, Tuple

from Orbitool.structures.spectrum import Spectrum

from ._noise import (getNoiseParams as _getNoiseParams,
                     getNoisePeaks as _getNoisePeaks,
                     noiseLODFunc as _noiseLODFunc,
                     denoiseWithParams as _denoiseWithParams)


def getNoiseParams(mass: np.ndarray, intensity: np.ndarray, quantile: float,
                   mass_dependent: bool, mass_points: np.ndarray,
                   mass_point_delta: float) -> Tuple[np.ndarray, List[bool], np.ndarray]:
    """
    return poly_coef, list[selected, params]
    """
    poly_coef, mass_point_rets = _getNoiseParams(mass, intensity, quantile, mass_dependent,
                                                 mass_points, mass_point_delta)
    slt: List[bool] = [ret[0] for ret in mass_point_rets]
    mass_point_params = [ret[1] for ret in mass_point_rets if ret[0]]
    mass_point_params = np.stack(mass_point_params)
    return poly_coef, slt, mass_point_params


def getNoisePeaks(mass: np.ndarray, intensity: np.ndarray, poly_coef: np.ndarray,
                  mass_point_params: np.ndarray, n_sigma: float):
    peak_mass, peak_intensity = _getNoisePeaks(
        mass, intensity, poly_coef, mass_point_params, n_sigma)
    return peak_mass, peak_intensity


def noiseLODFunc(mass: np.ndarray, poly_coef: np.ndarray,
                 mass_point_params: np.ndarray, n_sigma: float) -> Tuple[np.ndarray, np.ndarray]:
    noise, LOD = _noiseLODFunc(mass, poly_coef, mass_point_params, n_sigma)
    return noise, LOD


def denoiseWithParams(mass: np.ndarray, intensity: np.ndarray, poly_coef: np.ndarray,
                      mass_point_params: np.ndarray, n_sigma: bool, subtract: bool) -> Tuple[np.ndarray, np.ndarray]:
    """
    return mz, intensity
    """
    mass, intensity = _denoiseWithParams(mass, intensity, poly_coef,
                                         mass_point_params, n_sigma, subtract)
    return mass, intensity


def denoise(mass: np.ndarray, intensity: np.ndarray, quantile: float, n_sigma: float,
            mass_dependent: bool, mass_points: np.ndarray, mass_point_delta: float,
            subtract: bool) -> Tuple[np.ndarray, np.ndarray]:
    poly_coef, _, mass_point_params = getNoiseParams(mass, intensity, quantile, mass_dependent,
                                                     mass_points, mass_point_delta)
    mass, intensity = denoiseWithParams(mass, intensity, poly_coef,
                                        mass_point_params, n_sigma, subtract)
    return mass, intensity
