from datetime import datetime
from typing import Deque, Dict, List
import numpy as np
import pytest

from ..row_structure import BaseRowStructure
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
        some_array: NdArray[float, (-1, 2, 3)]

    a = Timeseries(
        time=[datetime.now()] * 10,
        intensity=[i * 2.5 for i in range(10)],
        bias=np.arange(10, dtype=float),
        some_array=np.empty((10, 2, 3), float)
    )

    f = H5File()
    f.write("t", a)
    b = f.read("t", Timeseries)
    assert a == b

    a.intensity.pop()
    with pytest.raises(Exception):
        f.write("exception", a)


def test_dataset_dict():
    class Item(BaseRowStructure):
        a: int
        b: float
        c: str
        d: datetime

    class DD(BaseDatasetStructure):
        dd: Dict[str, Item]
        a: int
        b: float
        c: str
        d: datetime

    values = dict(
        a=1, b=2.5, c="123", d=datetime.now()
    )

    a = DD(dd={str(i): Item(**values) for i in range(10)}, **values)

    f = H5File()
    f.write("dd", a)
    b = f.read("dd", DD)

    assert a == b


def test_dataset_compatibility():
    class Item(BaseRowStructure):
        a: int
        b: float
        c: str
        d: datetime

    class NewItem(BaseRowStructure):
        a: int
        b: float
        c: str
        # d: datetime # delete
        e: str = "123"

    class DD(BaseDatasetStructure):
        dd: Dict[str, Item]

    class NewDD(BaseDatasetStructure):
        dd: Dict[str, NewItem]

    values = dict(a=1, b=2.5, c="123", d=datetime.now())
    a = DD(dd={str(i): Item(**values) for i in range(10)}, **values)

    f = H5File()
    f.write("dd", a)
    b = f.read("dd", NewDD)
    assert b.dd["1"].e == "123"

