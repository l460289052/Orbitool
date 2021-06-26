from ...HDF5 import H5File
import numpy as np
from numpy import testing as nptest
import io
from datetime import datetime
import pytest
from .spectrum import Spectrum


def test_group():
    f = H5File()
    mz = np.arange(10)
    intensity = np.arange(10) + 1
    time = datetime(2000, 1, 1, 1, 1, 1)

    a = Spectrum(mz=mz, intensity=intensity, time=time)
    f["spectrum"] = a

    b :Spectrum= f["spectrum"]

    assert b.h5_type == a.h5_type
    nptest.assert_equal(mz, b.mz)
    nptest.assert_equal(intensity, b.intensity)
    assert time == b.time