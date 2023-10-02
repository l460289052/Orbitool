from typing import Optional, List
from array import array
import numpy as np

from ..spectrum import Spectrum, Peak, FittedPeak
from Orbitool.base import Array, NdArray
from .base import BaseInfo


def array_int():
    return array('i')


class PeakFitInfo(BaseInfo):
    spectrum: Spectrum = None

    raw_peaks: List[Peak] = []
    raw_split_num: Array['i'] = array('i')

    original_indexes: Array['i'] = array('i')
    peaks: List[FittedPeak] = []

    residual_mz: NdArray[float, -1] = None
    residual_intensity: NdArray[float, -1] = None

    shown_indexes: Array['i'] = []

    shown_mz: NdArray[float, -1] = None
    shown_intensity: NdArray[float, -1] = None
    shown_residual: NdArray[float, -1] = None
