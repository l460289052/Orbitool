import h5py
import io
from Orbitool.structures import HDF5
import pytest
import numpy as np
from datetime import datetime

from .spectrum import Spectrum, Spectra


@pytest.fixture
def h5file():
    return h5py.File(io.BytesIO(), 'w')


def init_spectrum(s: Spectrum, i=0):
    s.initialize(np.arange(i, i + 10), np.arange(i, i + 10),
                 datetime(1970 + i, 1, 1))


def check_spectrum(s: Spectrum, i=0):
    assert np.array_equal(s.mz, np.arange(i, i + 10))
    assert np.array_equal(s.intensity, np.arange(i, i + 10))
    assert np.array_equal(s.time, datetime(1970 + i, 1, 1))


def test_copy_from(h5file):
    s_m = Spectrum.create_at(h5file, 'm')
    init_spectrum(s_m)
    s_h = Spectrum.create_at(h5file, 's')
    s_h.copy_from(s_m)
    check_spectrum(s_h)


def init_list(l: HDF5.List):
    for i in range(10):
        s: Spectrum = l.append()
        init_spectrum(s, i)


def check_list(l: HDF5.List):
    for i in range(10):
        s: Spectrum = l[i]
        check_spectrum(s, i)
    for i, s in enumerate(l):
        check_spectrum(s, i)


# def init_massList(m: MassList):
#     data = [(10, 'C2H3;C5H10')] +\
#         [(i, str(i)) for i in range(10)]

#     m.masslist.extend(data)


# def check_massList(m: MassList):
#     ds = m.masslist.dataset
#     assert np.array_equal(ds['location'], np.concatenate(
#         [(10,), np.arange(10, dtype=np.float32)]))
#     assert np.array_equal(
#         ds['formulas'], ['C2H3;C5H10'] + [str(i) for i in range(10)])
#     data = [(10, 'C2H3;C5H10')] +\
#         [(i, str(i)) for i in range(10)]
#     for i, j in zip(ds[:], data):
#         assert i[0] == j[0] and i[1] == j[1]


def test_list_copy_from(h5file):
    l_m: HDF5.List = HDF5.List.create_at(h5file, 'm')
    l_m.initialize(Spectrum)
    init_list(l_m)
    l_h5: HDF5.List = HDF5.List.create_at(h5file, 'l')
    l_h5.copy_from(l_m)
    check_list(l_h5)


def init_dict(d: HDF5.Dict):
    for i in range(10):
        s: Spectrum = d.additem(str(i))
        init_spectrum(s, i)


def check_dict(d: HDF5.Dict):
    for k, v in d.items():
        check_spectrum(v, int(k))


def test_dict_copy_from(h5file):
    d_m: HDF5.Dict = HDF5.Dict.create_at(h5file, 'm')
    d_m.initialize(Spectrum)
    init_dict(d_m)
    d_h5: HDF5.Dict = HDF5.Dict.create_at(h5file, 'd')
    d_h5.copy_from(d_m)
    check_dict(d_h5)


def test_spectra_copy_from(h5file):
    s_m: Spectra = Spectra.create_at(h5file, 'm')
    s_m.initialize()

    init_list(s_m.spectra)
    s_h5 = Spectra.create_at(h5file, 's')
    s_h5.copy_from(s_m)
    check_list(s_h5.spectra)

