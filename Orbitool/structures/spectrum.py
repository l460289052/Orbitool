from .base import BaseStructure, Field
from datetime import datetime
import numpy as np


class Peak(BaseStructure):
    h5_type = "Peak"
    mz: np.ndarray
    intensity: np.ndarray
    splitNum: int


class FittedPeak(Peak):
    h5_type = "FittedPeak"
    fitted_param: np.ndarray
    peak_position: np.ndarray
    peak_intensity: np.ndarray
    formula_list: list


class Spectrum(BaseStructure):
    h5_type = "Spectrum"

    file_path: str
    mass: np.ndarray
    intensity: np.ndarray
    start_tTime: datetime
    end_time: datetime


class SpectrumList(BaseStructure):
    h5_type = "SpectrumList"


# class MassListItem
