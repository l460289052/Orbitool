from collections import deque
from datetime import datetime
from typing import Deque, List
import numpy as np
from numpy import testing as nptest
import pytest

from ..h5file import H5File
from ..extra_type_handlers import AttrNdArray, NdArray, Array
from ..dataset_structure import BaseDatasetStructure


def test_dataset_structure():
    class Spectrum(BaseDatasetStructure):
        index: NdArray[int, -1]
        mz: NdArray[float, -1]
        intensity: NdArray[float, -1]

        params: AttrNdArray[float, -1]

        attr1: int
        attr2: str

    a = Spectrum(
        index=np.arange(10),
        mz=np.empty(10, dtype=float),
        intensity=np.empty(10, dtype=float),
        params=np.empty(10, dtype=float),
        attr1=123,
        attr2="ddddddddddddddddddd")

    f = H5File()

    f.write("s", a)

    b = f.read("s", Spectrum)

    assert a == b


def test_dataset_list():
    class Timeseries(BaseDatasetStructure):
        time: List[datetime]
        intensity: Array["d"]

        bias: NdArray[float, -1]

    a = Timeseries(
        time=[datetime.now()] * 10,
        intensity=[i * 2.5 for i in range(10)],
        bias=np.arange(10, dtype=float)
    )

    f = H5File()
    f.write("t", a)
    b = f.read("t", Timeseries)
    assert a == b

    a.intensity.pop()
    with pytest.raises(Exception):
        f.write("exception", a)
