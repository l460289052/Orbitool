from typing import List
from datetime import datetime

import numpy as np
from numpy import testing as nptest

from ...base_structure import BaseStructure
from ...base_row import BaseRowItem
from ...HDF5 import H5File
from ..h5type_handlers import Row, AsciiLimit, NdArray


def test_dt():
    class TableItem(BaseRowItem):
        item_name = "test_item_name"

        int_test: int
        float_test: float
        str_test: str
        dt_test: datetime

    f = H5File()

    dt = datetime(2021, 6, 27, 7, 53, 41)
    item = TableItem(1, .1, "1" * 1000, dt_test=dt)

    f.write_table("table", TableItem, [item] * 10)

    items = f.read_table("table", TableItem)
    assert len(items) == 10
    item = items[0]
    assert item.int_test == 1
    assert item.float_test == .1
    assert item.str_test == "1" * 1000
    assert item.dt_test == dt


def test_ascii():
    class AsciiItem(BaseRowItem):
        item_name = "test_ascii_item"

        ascii: AsciiLimit[20]
    f = H5File()

    item = AsciiItem("123321")
    f.write_table("table", AsciiItem, [item] * 10)

    items = f.read_table("table", AsciiItem)

    assert len(items) == 10
    item = items[0]

    assert item.ascii == "123321"


def test_ndarray_1d():
    class Ndarray1DItem(BaseRowItem):
        item_name = "test_ndarray_1d"

        value: NdArray[int, 10]
    f = H5File()

    item = Ndarray1DItem(value=range(10))
    f.write_table("table", Ndarray1DItem, [item] * 10)

    items = f.read_table("table", Ndarray1DItem)
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10), item.value)


def test_ndarray_long():
    class Ndarray1DLongItem(BaseRowItem):
        item_name = "test_ndarray_1d_long"

        value: NdArray[int, -1]
    f = H5File()

    item = Ndarray1DLongItem(value=range(10))
    f.write_table("table", Ndarray1DLongItem, [item] * 10)

    items = f.read_table("table", Ndarray1DLongItem)
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10), item.value)

    item = Ndarray1DLongItem(value=range(10000))
    f.write_table("table", Ndarray1DLongItem, [item] * 10)
    items = f.read_table("table", Ndarray1DLongItem)
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10000), item.value)


def test_ndarray_hd():
    class NdarrayHDItem(BaseRowItem):
        item_name = "test_ndarray_hd"

        value: NdArray[float, (50, 10, 2, 2, 1)]
    f = H5File()

    item = NdarrayHDItem(value=np.empty((50, 10, 2, 2, 1)))
    f.write_table("table", NdarrayHDItem, [item] * 10)

    items = f.read_table("table", NdarrayHDItem)
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (50, 10, 2, 2, 1)


def test_ndarray_hd_long():
    class NdarrayHDLongItem(BaseRowItem):
        item_name = "test_ndarray_hd_long"

        value: NdArray[float, (5, 10, 2, 2, -1)]
    f = H5File()

    item = NdarrayHDLongItem(value=np.empty((5, 10, 2, 2, 1)))
    f.write_table("table", NdarrayHDLongItem, [item] * 10)

    items = f.read_table("table", NdarrayHDLongItem)
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (5, 10, 2, 2, 1)

    item = NdarrayHDLongItem(value=np.empty((5, 10, 2, 2, 37)))
    f.write_table("table", NdarrayHDLongItem, [item] * 10)

    items = f.read_table("table", NdarrayHDLongItem)
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (5, 10, 2, 2, 37)
