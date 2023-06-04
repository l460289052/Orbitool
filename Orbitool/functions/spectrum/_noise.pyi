from typing import List, Tuple
import numpy as np


def getNoisePeaks(mass: np.ndarray, intensity: np.ndarray, poly_coef: np.ndarray, std: float,
                  mass_point_params: np.ndarray, mass_points: np.ndarray, mass_point_deltas,
                  n_sigma: float):
    """
    return peak_mass, peak_intensity
    peak_mass: [peak1's mass point, peak2's mass point, ...]
    peak_intensity: [peak1's mass point intensity, ...]
    """
    pass


def getGlobalShownNoise(poly_coef: np.ndarray, n_sigma: float, std: float) -> Tuple[float, float]:
    """
    return noise, lod
    """
    pass


def updateGlobalParam(poly_coef: np.ndarray, n_sigma: float, noise: float, lod: float) -> Tuple[np.ndarray, float]:
    """
    return poly_coef, std
    """
    pass


def getNoiseParams(mz: np.ndarray, intensity: np.ndarray, quantile: float,
                   mass_dependent: float, mass_points: np.ndarray,
                   mass_point_deltas: np.ndarray) -> Tuple[np.ndarray, float, List[Tuple[bool, np.ndarray]]]:
    """
    return  poly_coef:np.ndarray, std, List[(useable: bool, params: np.ndarray)]
    """
    pass


def getNoiseLODFromParam(params: np.ndarray, n_sigma: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    return noise, lod
    """
    pass


def updateNoiseLODParam(params: np.ndarray, n_sigma: float, noise: float, lod: float) -> np.ndarray:
    """
    return params
    """
    pass


def noiseLODFunc(mass: np.ndarray, poly_coef: np.ndarray, std: float,
                 mass_point_params: np.ndarray, mass_points: np.ndarray,
                 mass_point_deltas: np.ndarray, n_sigma: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    return noise, LOD
    """
    pass


def denoiseWithParams(mass: np.ndarray, intensity: np.ndarray, poly_coef: np.ndarray, 
                      std: float, mass_point_params: np.ndarray, mass_points: np.ndarray,
                      mass_point_deltas: np.ndarray, n_sigma: float, subtract: bool) -> Tuple[np.ndarray, np.ndarray]:
    """
    return mz, intensity
    """
    pass
