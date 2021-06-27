import io
import h5py
import pytest
from numpy import testing as nptest

from .. import HDF5
from ..base import BaseTableItem

from ...utils.formula import Formula


formula_list = [Formula('C7H8O2'), Formula('C3H3Ti-'), Formula('CC[13]H[2]')]


class FormulaItem(BaseTableItem):
    item_name = "test_formula_item"

    formula: Formula


def test_formula():
    f = HDF5.H5File()

    f.write_table("table", FormulaItem, [FormulaItem(
        formula=formula) for formula in formula_list])

    formulas = f.read_table("table", FormulaItem)
    for f1, f2 in zip(formulas, formula_list):
        assert f1.formula == f2
