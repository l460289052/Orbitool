from utils.formula import Formula, FormulaHint

def test_formula1():
    s = "N[15]O3-"
    f: FormulaHint = Formula(s)
    assert f['O'] == 3
    assert f['N[15]'] == 1
    assert f['N'] == 1
    assert f.charge == -1
