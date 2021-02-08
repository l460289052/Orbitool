from typing import Tuple, List, Iterable
import numpy as np

from ._average import mergeSpectra as _mergeSpectra


def mergeSpectra(mass1: np.ndarray, intensity1: np.ndarray, mass2: np.ndarray,
                 intensity2: np.ndarray, weight1: float, weight2: float,
                 rtol: float = 1e-6, drop_input: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    mass, intensity = _mergeSpectra(mass1, intensity1, mass2, intensity2,
                                    weight1, weight2, rtol, drop_input)
    return mass, intensity


def averageSpectra(mass_intensity_weight_list: Iterable[Tuple[np.ndarray, np.ndarray, float]],
                   rtol: float = 1e-6, drop_input: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    it = iter(mass_intensity_weight_list)
    mass_sum, intensity_sum, weight_sum = next(it)
    for mass, intensity, weight in it:
        mass_sum, intensity_sum = mergeSpectra(mass_sum, intensity_sum, mass,
                                               intensity, weight_sum, weight, rtol, drop_input)
        weight_sum += weight
    return mass_sum, intensity_sum
