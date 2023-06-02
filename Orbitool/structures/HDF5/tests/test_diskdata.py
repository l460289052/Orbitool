from ..h5diskdata import DiskDict, DiskList, BaseDiskDataProxy

from .spectrum import Spectrum
from ..h5obj import H5File
from numpy import testing as nptest
import numpy as np
from datetime import datetime


class DiskProxy(BaseDiskDataProxy):
    spectrum_dict = DiskDict(Spectrum)
    spectrum_list = DiskList(Spectrum)


def test_dict():
    f = H5File()
    tmp = H5File()
    fo = f._obj
    to = tmp._obj

    proxy = DiskProxy(fo, to)

    key: str = "spectrum_dict"
    assert key in fo

    for i in range(10):
        intensity = mz = np.ones(10) * i
        proxy.spectrum_dict[str(i)] = Spectrum(mz=mz, intensity=intensity,
                                               time=datetime(2000, 1, i + 1))

    assert key in to

    assert len(fo[key]) == 0
    assert len(to[key]) == 10
    assert len(proxy.spectrum_dict) == 10

    for i, spectrum in proxy.spectrum_dict.items():
        i = int(i)
        nptest.assert_equal(spectrum.mz, np.ones(10) * i)
        assert datetime(2000, 1, i + 1) == spectrum.time

    for i in range(0, 10, 2):
        del proxy.spectrum_dict[i]

    proxy.save_to_disk()

    assert key in to
    assert len(to[key]) == 0
    assert len(fo[key]) == 5
    assert len(proxy.spectrum_dict) == 5
    assert set(fo[key].keys()) == set(map(str, range(1, 10, 2)))

    proxy.spectrum_dict.clear()
    proxy.save_to_disk()
    assert len(fo[key]) == 0

def test_list():
    f = H5File()
    tmp = H5File()
    fo = f._obj
    to = tmp._obj

    proxy = DiskProxy(fo, to)

    key: str = "spectrum_list"
    assert key in fo

    for i in range(10):
        intensity = mz = np.ones(10) * i
        proxy.spectrum_list.append(Spectrum(mz=mz, intensity=intensity,
                                               time=datetime(2000, 1, i + 1)))

    spectrum_list = list(proxy.spectrum_list)

    assert key in to

    assert len(fo[key]) == 0
    assert len(to[key]) == 10
    assert len(proxy.spectrum_list) == 10

    proxy.save_to_disk()

    for i, spectrum in enumerate(proxy.spectrum_list):
        nptest.assert_equal(spectrum.mz, np.ones(10) * i)
        assert datetime(2000, 1, i + 1) == spectrum.time

    proxy.spectrum_list = spectrum_list

    assert len(fo[key]) == 10
    assert len(to[key]) == 10
    assert len(proxy.spectrum_list) == 10

    proxy.save_to_disk()

    assert len(fo[key]) == 10
    assert len(to[key]) == 0
    assert len(proxy.spectrum_list) == 10

    for i, spectrum in enumerate(proxy.spectrum_list):
        nptest.assert_equal(spectrum.mz, np.ones(10) * i)
        assert datetime(2000, 1, i + 1) == spectrum.time

    for i in reversed(range(0, 10, 2)):
        del proxy.spectrum_list[i]

    proxy.save_to_disk()

    assert key in to
    assert len(to[key]) == 0
    assert len(fo[key]) == 5
    assert len(proxy.spectrum_list) == 5
    for i, spectrum in enumerate(proxy.spectrum_list):
        i = 2 * i + 1
        nptest.assert_equal(spectrum.mz, np.ones(10) * i)
        assert datetime(2000, 1, i + 1) == spectrum.time

    proxy.spectrum_list.clear()
    proxy.save_to_disk()
    assert len(fo[key]) == 0