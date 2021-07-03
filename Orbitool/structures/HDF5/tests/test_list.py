from ..h5structure_list import StructureList
from .spectrum import Spectrum
from ..h5obj import H5File
from numpy import testing as nptest
import numpy as np
from datetime import datetime


class FileList(H5File):
    spectrum_list = StructureList(Spectrum)


def test_list():
    f = FileList()
    l = f.spectrum_list
    for i in range(10):
        intensity = mz = np.ones(10) * i
        l.h5_append(Spectrum(mz=mz, intensity=intensity,
                             time=datetime(2000, 1, i + 1)))

    for index, spectrum in enumerate(l):
        nptest.assert_equal(spectrum.mz, np.ones(10) * index)
        assert datetime(2000, 1, index + 1) == spectrum.time
