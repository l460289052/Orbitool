from typing import List, Tuple
import numpy as np


def getNoisePeaks(mass: np.ndarray, intensity: np.ndarray, poly_coef: np.ndarray,
                  mass_point_params: np.ndarray, n_sigma: float):
    """
    return peak_mass, peak_intensity
    peak_mass: [peak1's mass point, peak2's mass point, ...]
    peak_intensity: [peak1's mass point intensity, ...]
    """
    pass


def noiseLODFunc(mass: np.ndarray, poly_coef: np.ndarray,
                 mass_point_params: np.ndarray, n_sigma: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    return noise, LOD
    """
    pass


def denoiseWithParams(mass: np.ndarray, intensity: np.ndarray, poly_coef: np.ndarray,
                      mass_point_params: np.ndarray, n_sigma: bool, subtract: bool) -> Tuple[np.ndarray, np.ndarray]:
    """
    return mz, intensity
    """
    pass
