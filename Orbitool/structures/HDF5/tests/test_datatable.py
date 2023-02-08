from typing import List
from datetime import datetime

import numpy as np
from numpy import testing as nptest

from Orbitool.structures.HDF5.h5type_handlers.row_handler import DictRow

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

    row = Row((TableItem, ))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]
    assert item.int_test == 1
    assert item.float_test == .1
    assert item.str_test == "1" * 1000
    assert item.dt_test == dt


def test_dict_dt():
    class TableItem(BaseRowItem):
        item_name = "test_dict_item_name"

        int_test: int
        float_test: float
        str_test: str
        dt_test: datetime
    f = H5File()
    dt = datetime(2021, 6, 27, 7, 53, 41)
    item = TableItem(1, .1, "1" * 1000, dt_test=dt)

    dr = DictRow((str, TableItem))

    dr.write_to_h5(f._obj, "dict", {str(i): item for i in range(10)})

    items: DictRow[str, TableItem] = dr.read_from_h5(f._obj, "dict")

    assert len(items) == 10
    assert set(items.keys()) == set(map(str, range(10)))
    item = items["0"]
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
    row = Row((AsciiItem, ))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")

    assert len(items) == 10
    item = items[0]

    assert item.ascii == "123321"


def test_ndarray_1d():
    class Ndarray1DItem(BaseRowItem):
        item_name = "test_ndarray_1d"

        value: NdArray[int, 10]
    f = H5File()

    item = Ndarray1DItem(value=range(10))
    row = Row((Ndarray1DItem,))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10), item.value)


def test_ndarray_long():
    class Ndarray1DLongItem(BaseRowItem):
        item_name = "test_ndarray_1d_long"

        value: NdArray[int, -1]
    f = H5File()

    item = Ndarray1DLongItem(value=range(10))
    row = Row((Ndarray1DLongItem,))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10), item.value)

    item = Ndarray1DLongItem(value=range(10000))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]

    nptest.assert_array_equal(range(10000), item.value)


def test_ndarray_hd():
    class NdarrayHDItem(BaseRowItem):
        item_name = "test_ndarray_hd"

        value: NdArray[float, (50, 10, 2, 2, 1)]
    f = H5File()

    item = NdarrayHDItem(value=np.empty((50, 10, 2, 2, 1)))
    row = Row((NdarrayHDItem,))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (50, 10, 2, 2, 1)


def test_ndarray_hd_long():
    class NdarrayHDLongItem(BaseRowItem):
        item_name = "test_ndarray_hd_long"

        value: NdArray[float, (5, 10, 2, 2, -1)]
    f = H5File()

    item = NdarrayHDLongItem(value=np.empty((5, 10, 2, 2, 1)))
    row = Row((NdarrayHDLongItem))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (5, 10, 2, 2, 1)

    item = NdarrayHDLongItem(value=np.empty((5, 10, 2, 2, 37)))
    row.write_to_h5(f._obj, "table", [item] * 10)

    items = row.read_from_h5(f._obj, "table")
    assert len(items) == 10
    item = items[0]

    assert item.value.shape == (5, 10, 2, 2, 37)
