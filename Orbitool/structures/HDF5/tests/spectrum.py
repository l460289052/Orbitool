from datetime import datetime

import numpy as np

from ...base import BaseStructure, dataclass
from dataclasses import field as ff

type_name = 'testSpectrum'


class Spectrum(BaseStructure):
    h5_type = type_name
    mz: np.ndarray = None
    intensity: np.ndarray = None
    time: datetime = None
