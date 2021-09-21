import io
from datetime import datetime
from typing import List

import numpy as np
import pytest
from numpy import testing as nptest

from ...base import  field
from ...base_structure import BaseStructure
from ...HDF5 import H5File
from .spectrum import Spectrum


def test_group():
    f = H5File()
    mz = np.arange(10)
    intensity = np.arange(10) + 1
    time = datetime(2000, 1, 1, 1, 1, 1)

    a = Spectrum(mz, intensity, time)
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

    c1 = Child(1)
    c2 = Child(value=2)
    father = Father(3, c1, c2)
    f.write("father", father)

    t: Father = f.read("father")

    assert t.value == 3
    assert t.c1.value == 1
    assert t.c2.value == 2


class SomeList(BaseStructure):
    h5_type = "test some list"
    value_a: List[int] = field(list)
    value_b: List[float] = field(list)
    value_c: List[Spectrum] = field(list)


def test_some_list_a():
    f = H5File()

    some_list = SomeList(value_a=list(range(1000)), value_b=[
                         i / 10. for i in range(5)])

    f.write("list", some_list)

    some_list: SomeList = f.read("list")
    assert some_list.value_a == list(range(1000))
    assert some_list.value_b == [i / 10. for i in range(5)]
