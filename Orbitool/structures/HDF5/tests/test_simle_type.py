from ...HDF5 import H5File
from ...base import BaseStructure
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
    f.write("spectrum", a)

    b: Spectrum = f.read("spectrum")

    assert b.h5_type == a.h5_type
    nptest.assert_equal(mz, b.mz)
    nptest.assert_equal(intensity, b.intensity)
    assert time == b.time


def test_structure():
    class Child(BaseStructure):
        h5_type = "test_child"
        value: int

    class Father(BaseStructure):
        h5_type = "test_father"
        value: int
        c1: Child
        c2: Child

    f = H5File()

    c1 = Child(value=1)
    c2 = Child(value=2)
    father = Father(value=3, c1=c1, c2=c2)
    f.write("father", father)

    t: Father = f.read("father")

    assert t.value == 3
    assert t.c1.value == 1
    assert t.c2.value == 2
