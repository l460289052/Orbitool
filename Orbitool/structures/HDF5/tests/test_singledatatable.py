import io

import numpy as np
from numpy import testing as nptest

import pytest
import h5py
from Orbitool.structures import HDF5
from Orbitool.structures.HDF5 import datatable


@pytest.fixture
def h5file():
    return h5py.File(io.BytesIO(), 'w')


def init_sdt(sdt: datatable.SingleDatatable):
    sdt.extend(range(10))
    sdt[2:7:2] = [-1] * 3


def check_sdt(sdt: datatable.SingleDatatable):
    a = np.arange(10, dtype=np.int32)
    a[2:7:2] = [-1] * 3
    nptest.assert_equal(sdt.get_column(), a)


def test_singledatatable(h5file: h5py.File):
    sdt = datatable.SingleDatatable.create_at(h5file, 'sdt', datatable.Int32)
    init_sdt(sdt)
    check_sdt(sdt)


def test_copy(h5file: h5py.File):
    dt = datatable.SingleDatatable.create_at(h5file, 'dt', datatable.Int32)
    init_sdt(dt)

    dtto = datatable.SingleDatatable.create_at(h5file, 'dtto', datatable.Int32)
    dtto.copy_from(dt)
    check_sdt(dtto)
