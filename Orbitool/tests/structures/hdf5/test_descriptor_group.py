import sys
import numpy as np
from Orbitool.structures import HDF5
from h5py import File
import io
import pytest
from datetime import datetime


@pytest.fixture
def h5file():
    return File(io.BytesIO(), 'w')


def test_subclass_type():
    with pytest.raises(AssertionError):
        class Spectrum(HDF5.Group):
            pass


type_name = 'Spectrum'


class Spectrum(HDF5.Group):
    h5_type = HDF5.RegisterType(type_name)
    mz = HDF5.SmallNumpy()
    intensity = HDF5.BigNumpy()
    time = HDF5.Datetime()

    def initialize(self, mz, intensity, time):
        self.mz = mz
        self.intensity = intensity
        self.time = time


def test_group(h5file: File):
    mz = np.arange(10)
    intensity = np.arange(10) + 1
    time = datetime(2000, 1, 1, 1, 1, 1)

    a = Spectrum.create_at(h5file, 'spec')
    a.initialize(mz, intensity, time)

    with pytest.raises(NotImplementedError):
        a.h5_type = "123"
    assert a.h5_type.attr_type_name == a.h5_type.type_name and a.h5_type.type_name == type_name

    b = Spectrum(h5file['spec'])

    assert np.array_equal(b.mz, np.arange(10))
    assert np.array_equal(b.intensity, np.arange(10) + 1)
    assert b.time == time


def test_list(h5file: File):
    l: HDF5.List = HDF5.List.create_at(h5file, 'list')
    l.initialize(Spectrum)
    for i in range(10):
        s: Spectrum = l.append()
        s.initialize([i] * 10, [i] * 10, datetime(1970 + i, 1, 1))

    r = HDF5.List(h5file['list'])

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
    assert np.array_equal(r[0].mz, [0]*10)


def test_dict(h5file: File):
    d: HDF5.Dict = HDF5.Dict.create_at(h5file, 'dict')
    d.initialize(Spectrum)
    for i in range(10):
        s: Spectrum = d.additem(str(i))
        s.initialize([i] * 10, [i] * 10, datetime(1970 + i, 1, 1))

    dd = HDF5.Dict(h5file['dict'])

    assert all(k1 == str(k2) for k1, k2 in zip(dd.keys(), range(10)))

    for k, v in dd.items():
        v: Spectrum
        assert v.h5_type.type_name == type_name
        assert np.array_equal(v.mz, [int(k)] * 10)
        assert np.array_equal(v.mz, np.array([int(k)] * 10))
        assert v.time == datetime(1970+int(k), 1, 1)


def test_group_descriptor(h5file: File):
    class Spectra(HDF5.Group):
        h5_type = HDF5.RegisterType('Spectra')
        spectra: HDF5.List = HDF5.List.descriptor(Spectrum)

    s: Spectra = Spectra.create_at(h5file, 's')
    m: Spectrum = s.spectra.append()
    m.initialize(np.arange(10), np.arange(20), datetime(1970, 1, 1))

    m.intensity = np.arange(10)

    m: Spectrum = s.spectra[0]
    assert np.array_equal(m.mz, range(10))
    assert np.array_equal(m.intensity, range(10))
