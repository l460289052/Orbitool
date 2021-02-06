import sys
import numpy as np
from Orbitool.structures import HDF5
import io
from datetime import datetime
import pytest

from .spectrum import Spectrum, type_name, Spectra


def test_group(location):
    mz = np.arange(10)
    intensity = np.arange(10) + 1
    time = datetime(2000, 1, 1, 1, 1, 1)

    a = Spectrum.create_at(location, 'spec')
    a.initialize(mz, intensity, time)

    with pytest.raises(NotImplementedError):
        a.h5_type = "123"
    assert a.h5_type.attr_type_name == a.h5_type.type_name == type_name

    b = Spectrum(location['spec'])

    assert np.array_equal(b.mz, np.arange(10))
    assert np.array_equal(b.intensity, np.arange(10) + 1)
    assert b.time == time


def test_list(location):
    l: HDF5.List = HDF5.List.create_at(location, 'list', Spectrum)
    l.initialize()
    for i in range(10):
        s: Spectrum = l.append()
        s.initialize([i] * 10, [i] * 10, datetime(1970 + i, 1, 1))

    r = HDF5.List(location['list'])

    for i, spectrum in enumerate(r):
        spectrum: Spectrum
        assert spectrum.h5_type.type_name == type_name
        assert np.array_equal(spectrum.mz, [i] * 10)
        assert np.array_equal(spectrum.intensity, np.array([i] * 10))
        assert spectrum.time == datetime(1970 + i, 1, 1)

    del l[0]
    assert np.array_equal(r[0].mz, [1] * 10)
    s: Spectrum = l.insert(0)
    s.initialize([0] * 10, [0] * 10, datetime(1970, 1, 1))
    assert np.array_equal(r[-1].mz, [9] * 10)
    assert np.array_equal(r[0].mz, [0] * 10)


def test_dict(location):
    d: HDF5.Dict = HDF5.Dict.create_at(location, 'dict', Spectrum)
    d.initialize()
    for i in range(10):
        s: Spectrum = d.additem(str(i))
        s.initialize([i] * 10, [i] * 10, datetime(1970 + i, 1, 1))

    dd = HDF5.Dict(location['dict'])

    assert all(k1 == str(k2) for k1, k2 in zip(dd.keys(), range(10)))

    for k, v in dd.items():
        v: Spectrum
        assert v.h5_type.type_name == type_name
        assert np.array_equal(v.mz, [int(k)] * 10)
        assert np.array_equal(v.mz, np.array([int(k)] * 10))
        assert v.time == datetime(1970 + int(k), 1, 1)


def test_group_descriptor(location):
    s: Spectra = Spectra.create_at(location, 's')
    m: Spectrum = s.spectra.append()
    m.initialize(np.arange(10), np.arange(20), datetime(1970, 1, 1))

    m.intensity = np.arange(10)

    m: Spectrum = s.spectra[0]
    assert np.array_equal(m.mz, range(10))
    assert np.array_equal(m.intensity, range(10))


def test_ref_attr(location):
    s: Spectra = Spectra.create_at(location, 's')
    m: Spectrum = s.spectra.append()
    m.initialize(np.arange(10), np.arange(10), datetime(1970, 1, 1))

    m.father = s

    f = m.father
    mm = f.spectra[0]
    assert np.array_equal(mm.mz, range(10))
    assert np.array_equal(mm.intensity, range(10))
