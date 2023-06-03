from typing import Optional, List
from array import array
import numpy as np

from ..structures import BaseStructure, field, Row
from ..structures.HDF5 import Array
from ..structures.spectrum import Spectrum, FittedPeak, Peak
from .base import BaseInfo


def array_int():
    return array('i')


class PeakFitInfo(BaseInfo):
    h5_type = "peak fit tab"
    spectrum: Spectrum = None

    raw_peaks: Row[Peak] = field(list)
    raw_split_num: Array[int] = field(array_int)

    original_indexes: Array[int] = field(array_int)
    peaks: Row[FittedPeak] = field(list)

    residual_mz: np.ndarray = None
    residual_intensity: np.ndarray = None

    shown_indexes: Array[int] = field(array_int)

    shown_mz: np.ndarray = None
    shown_intensity: np.ndarray = None
    shown_residual: np.ndarray = None
