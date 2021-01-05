import sys
import numpy as np
from Orbitool import HDF5
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
    intensity = HDF5.SmallNumpy()
    time = HDF5.Datetime()

    @classmethod
    def create_at(cls, mz, intensity, time, *args, **kwargs):
        ins = super().create_at(*args, **kwargs)
        ins.mz = mz
        ins.intensity = intensity
        ins.time = time
        return ins


def test_group(h5file: File):
    mz = np.arange(10)
    intensity = np.arange(10) + 1
    time = datetime(2000, 1, 1, 1, 1, 1)

    a = Spectrum.create_at(mz, intensity, time, location=h5file, key='spec')

    with pytest.raises(NotImplementedError):
        a.h5_type = "123"
    assert a.h5_type.attr_type_name == a.h5_type.type_name and a.h5_type.type_name == type_name

    b = Spectrum(h5file['spec'])

    assert np.array_equal(b.mz, np.arange(10))
    assert np.array_equal(b.intensity, np.arange(10) + 1)
    assert b.time == time


def test_list(h5file: File):
    l: HDF5.List = HDF5.List.create_at(
        location=h5file, key='list', child_type=Spectrum)
    for i in range(10):
        location, key = l.get_append_location()
        s: Spectrum = Spectrum.create_at(
            [i] * 10, [i] * 10, datetime(1970 + i, 1, 1), location, key)

    r = HDF5.List(h5file['list'])

    for i, spectrum in enumerate(l):
        spectrum: Spectrum
        assert spectrum.h5_type.type_name == type_name
        assert np.array_equal(spectrum.mz, [i] * 10)
        assert np.array_equal(spectrum.intensity, [i] * 10)
        assert spectrum.time == datetime(1970 + i, 1, 1)
