import io
from datetime import datetime, timedelta

import numpy as np
from numpy import testing as nptest
import pytest
import h5py

from Orbitool.structures import HDF5
from Orbitool.structures.HDF5 import datatable


@pytest.fixture
def h5file():
    return h5py.File(io.BytesIO(), 'w')


class file(datatable.DatatableItem):
    item_name = "test_datatable_file"

    path = datatable.str_utf8()
    startDatetime = datatable.Datatime64s()
    endDatetime = datatable.Datatime64s()
    append = datatable.str_ascii_limit(length=10)


def init_dt(dt):
    dtn = datetime(2000, 1, 1, 2, 3, 4)
    dtt = dtn + timedelta(1)
    f = file('123', dtn, append="123321", endDatetime=dtt)
    dt.extend([f] * 12)

    f = [file(str(i), dtn, dtt, '123') for i in range(6)]

    dt[::2] = f

    del dt[:2]


def check_dt(dt: datatable.Datatable):
    dtn = datetime(2000, 1, 1, 2, 3, 4)
    dtt = dtn + timedelta(1)

    paths = sum(([str(i), '123'] for i in range(1, 6)), [])
    nptest.assert_array_equal(dt.get_column('path'), paths)
    appends = ["123", "123321"] * 5
    nptest.assert_array_equal(dt.get_column('append'), appends)

    it = iter(dt)
    f: file = next(it)
    assert f.path == '1'
    assert f.startDatetime == dtn
    assert f.endDatetime == dtt
    assert f.append == "123"

    f: file = next(it)
    assert f.path == '123'
    assert f.startDatetime == dtn
    assert f.endDatetime == dtt
    assert f.append == "123321"


def test_datatable(h5file: h5py.File):
    dt = datatable.Datatable.create_at(h5file, 'dt', file)
    init_dt(dt)
    check_dt(dt)


def test_copy(h5file: h5py.File):
    dt = datatable.Datatable.create_at(h5file, 'dt', file)
    init_dt(dt)

    dtto = datatable.Datatable.create_at(h5file, 'dtto', file)
    dtto.copy_from(dt)
    check_dt(dtto)