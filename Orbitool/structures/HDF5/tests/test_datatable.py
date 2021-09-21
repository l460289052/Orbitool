from typing import List
from datetime import datetime

import numpy as np
from numpy import testing as nptest

from ...base import BaseRowItem
from ...HDF5 import H5File
from ..h5datatable import TableConverter, AsciiLimit, Int32, Ndarray


class TableItem(BaseRowItem):
    item_name = "test_item_name"

    int_test: int
    float_test: float
    str_test: str
    dt_test: datetime


def test_dt():
    f = H5File()

    dt = datetime(2021, 6, 27, 7, 53, 41)
    item = TableItem(int_test=1, float_test=.1,
                     str_test="1" * 1000, dt_test=dt)

    f.write_table("table", TableItem, [item] * 10)

    items = f.read_table("table", TableItem)
    assert len(items) == 10
    item = items[0]
    assert item.int_test == 1
    assert item.float_test == .1
    assert item.str_test == "1" * 1000
    assert item.dt_test == dt


class AsciiItem(BaseRowItem):
    item_name = "test_ascii_item"

    int32: Int32
    ascii: AsciiLimit[20]


def test_ascii():
    f = H5File()

    item = AsciiItem(int32=12, ascii="123321")
    f.write_table("table", AsciiItem, [item] * 10)

    items = f.read_table("table", AsciiItem)

    assert len(items) == 10
    item = items[0]

    assert item.int32 == 12
    assert item.ascii == "123321"


class Ndarray1DItem(BaseRowItem):
    item_name = "test_ndarray_1d"

    value: Ndarray[int, 10]


def test_ndarray_1d():
    f = H5File()

    item = Ndarray1DItem(value=range(10))
    f.write_table("table", Ndarray1DItem, [item] * 10)

    items = f.read_table("table", Ndarray1DItem)
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10), item.value)


class Ndarray1DLongItem(BaseRowItem):
    item_name = "test_ndarray_1d_long"

    value: Ndarray[int, -1]


def test_ndarray_long():
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


class NdarrayHDItem(BaseRowItem):
    item_name = "test_ndarray_hd"

    value: Ndarray[float, (50, 10, 2, 2, 1)]


def test_ndarray_hd():
    f = H5File()

    item = NdarrayHDItem(value=np.empty((50, 10, 2, 2, 1)))
    f.write_table("table", NdarrayHDItem, [item] * 10)

    items = f.read_table("table", NdarrayHDItem)
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (50, 10, 2, 2, 1)


class NdarrayHDLongItem(BaseRowItem):
    item_name = "test_ndarray_hd_long"

    value: Ndarray[float, (5, 10, 2, 2, -1)]


def test_ndarray_hd_long():
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
