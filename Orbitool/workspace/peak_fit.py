from typing import Optional, List
from array import array
import numpy as np

from ..structures.base import BaseStructure, Field
from ..structures.spectrum import Spectrum, FittedPeak, Peak


class PeakFitInfo(BaseStructure):
    h5_type = "peak fit tab"
    spectrum: Optional[Spectrum] = None

    raw_peaks: List[Peak] = Field(default_factory=list)
    raw_split_num = array('i')

    original_indexes = array('i')
    peaks: List[FittedPeak] = Field(default_factory=list)

    residual_mz: Optional[np.ndarray] = None
    residual_intensity: Optional[np.ndarray] = None

    shown_indexes = array('i')

    shown_mz: Optional[np.ndarray] = None
    shown_intensity: Optional[np.ndarray] = None
    shown_residual: Optional[np.ndarray] = None
