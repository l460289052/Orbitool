from datetime import datetime

import h5py
import numpy as np

from ... import HDF5
from ...base import BaseStructure

type_name = 'testSpectrum'


class Spectrum(BaseStructure):
    h5_type = type_name
    mz: np.ndarray
    intensity: np.ndarray
    time: datetime
