import numpy as np
from datetime import datetime
from numpy import testing as nptest
from pydantic import TypeAdapter, ValidationError
import pytest
from .. import BaseStructure, H5File, NdArray
from ..structure import AnnotationError
from .spectrum import Spectrum


def test_validate():
    data = np.arange(10)
    with pytest.raises(AnnotationError):
        TypeAdapter(NdArray[int, 1, 2])
    with pytest.raises(AnnotationError):
        TypeAdapter(NdArray[int, (-1, -1, 10, 10)])
    assert (TypeAdapter(NdArray).validate_python(data) == data).all()

    assert (TypeAdapter(NdArray[int]).validate_python(data) == data).all()

    assert (TypeAdapter(NdArray[int, -1]).validate_python(data) == data).all()

    assert (TypeAdapter(NdArray[int, 10]).validate_python(
        data.astype(float)) == data).all()

    TypeAdapter(NdArray[int, (11, 10)]).validate_python(
        np.array([data] * 11))
    TypeAdapter(NdArray[int, (-1, 10)]).validate_python(
        np.array([data] * 11))
    with pytest.raises(ValidationError):
        TypeAdapter(NdArray[int, (10, -1)]).validate_python(
            np.array([data] * 11))
    with pytest.raises(ValidationError):
        TypeAdapter(NdArray[int, (10, 10)]).validate_python(
            np.array([data] * 11))


def test_np():
    f = H5File()
    mz = np.arange(10)
    intensity = np.arange(10) + 1
    time = datetime(2000, 1, 1, 1, 1, 1)

    a = Spectrum(mz=mz, intensity=intensity, time=time)
    f.write("spectrum", a)

    b = f.read("spectrum", Spectrum)
    assert b is not None

    nptest.assert_equal(mz, b.mz)
    nptest.assert_equal(intensity, b.intensity)
    assert time == b.time


def test_dt():
    with pytest.raises(AnnotationError):
        class DT(BaseStructure):
            dts: NdArray[datetime]
    with pytest.raises(AnnotationError):
        class DT(BaseStructure):
            dts: NdArray["datetime64[ns]"]

    class DT(BaseStructure):
        dts: NdArray["datetime64[us]"]

    f = H5File()

    dt = datetime(2020, 1, 1, 1, 1, 1)
    a = DT(dts=None)
    assert a.dts is None
    a.dts = [dt] * 10

    f.write("dt", a)
    b = f.read("dt", DT)

    assert b.dts.dtype == np.dtype("datetime64[us]")
    assert all(dt == t for t in b.dts.astype(datetime))
