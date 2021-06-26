import io
import h5py
import pytest
from numpy import testing as nptest

from .. import HDF5
from ..HDF5 import datatable

from ...utils.formula import Formula
from .. import FormulaDatatableDescriptor


@pytest.fixture
def h5file():
    return h5py.File(io.BytesIO(), 'w')


formula_list = [Formula('C7H8O2'), Formula('C3H3Ti-'), Formula('CC[13]H[2]')]


def init_dt(dt: datatable.Datatable):
    dt.extend(formula_list)
    dt.extend([Formula()])
    dt[-1] = Formula('C3H')
    dt.extend([Formula()] * len(formula_list))
    dt[-len(formula_list):] = formula_list


def check_dt(dt: datatable.Datatable):
    nptest.assert_equal(formula_list, dt.get_column()[:len(formula_list)])
    assert dt[-1 - len(formula_list)] == Formula('C3H')
    nptest.assert_equal(formula_list, list(dt[-len(formula_list):]))


def test(h5file: h5py.File):
    dt = datatable.SingleDatatable.create_at(
        h5file, "f", FormulaDatatableDescriptor)

    init_dt(dt)
    check_dt(dt)
