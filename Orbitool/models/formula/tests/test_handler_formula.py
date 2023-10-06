from pydantic import BaseModel, ValidationError
import pytest
from numpy import testing as nptest

from Orbitool.base import BaseRowStructure, H5File
from Orbitool.base.structure import BaseStructure
from ..h5handlers import *

formula_list = [Formula('C7H8O2'), Formula('C3H3Ti-'), Formula('CC[13]H[2]')]


class FormulaItem(BaseRowStructure):
    formula: FormulaType


def test_pydantic_validate():
    class Formulas(BaseModel):
        formula: FormulaType
    Formulas(formula="CH4")

    with pytest.raises(ValidationError):
        Formulas(formula=123)


def test_formula():
    f = H5File()

    f.write("fs", [FormulaItem(formula=formula)
            for formula in formula_list], List[FormulaItem])

    formulas = f.read("fs", List[FormulaItem])
    for f1, f2 in zip(formulas, formula_list):
        assert f1.formula == f2


class FormulasItem(BaseRowStructure):
    formulas: FormulaList = []


def test_formulas():
    f = H5File()

    f.write("fss", [FormulasItem(
        formulas=formula_list)] * 10, List[FormulasItem])

    formulas_table = f.read("fss", List[FormulasItem])
    for formulas in formulas_table:
        assert formulas.formulas == formula_list

    f.write("fss", [FormulasItem(
        formulas=[])] * 10, List[FormulasItem])

    formulas_table = f.read("fss", List[FormulasItem])
    for formulas in formulas_table:
        assert formulas.formulas == []

class FormulasAttr(BaseStructure):
    formulas: FormulaList = []


def test_formulas_attr():
    f = H5File()

    f.write("fss", FormulasAttr(
        formulas=formula_list), FormulasAttr)

    formulas = f.read("fss", FormulasAttr)
    assert formulas.formulas == formula_list

    f.write("fss", FormulasAttr(
        formulas=[]), FormulasAttr)

    formulas = f.read("fss", FormulasAttr)
    assert formulas.formulas == []
