from typing import List
from datetime import datetime

from ...base import BaseTableItem
from ...HDF5 import H5File
from ..h5datatable import TableConverter, AsciiLimit, Int32


class TableItem(BaseTableItem):
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


class AsciiItem(BaseTableItem):
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
