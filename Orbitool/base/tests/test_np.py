import numpy as np
from datetime import datetime, timedelta
from numpy import testing as nptest
from pydantic import TypeAdapter, ValidationError
import pytest
from .. import BaseStructure, H5File, NdArray, AttrNdArray
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

    class DT(BaseStructure):
        dts: NdArray["datetime64[ns]"]

    class DT(BaseStructure):
        dts: NdArray["datetime64[us]"]

    f = H5File()

    dt = datetime(2020, 1, 1, 1, 1, 1)
    a = DT(dts=np.array([dt] * 10, "datetime64[us]"))

    f.write("dt", a)
    b = f.read("dt", DT)

    assert b.dts.dtype == np.dtype("datetime64[us]")
    assert all(dt == t for t in b.dts.astype(datetime))


def test_attr():
    class TA(BaseStructure):
        i: AttrNdArray[int, -1]
        s: AttrNdArray[str, -1]
        d: AttrNdArray['datetime64[us]', -1]

    ta = TA(
        i=np.arange(10),
        s=['123'] * 10,
        d=[datetime.now() + timedelta(i) for i in range(10)]
    )

    f = H5File()

    f.write("ta", ta)

    tb = f.read("ta", TA)

    assert ta == tb


def test_unicode_str():
    class US(BaseStructure):
        s: NdArray[str, -1]
        b: NdArray[bytes, -1]
    a = US(
        s=np.array(["质谱"] * 10, str),
        b=np.array([b"123"] * 10, bytes)
    )

    f = H5File()

    f.write("ta", a)

    b = f.read("ta", US)

    assert a == b
