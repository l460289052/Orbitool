import copy
import pytest
import csv
import pathlib

from .. import Formula, RestrictedCalc


def init_calc():
    return RestrictedCalc()


calc = pytest.fixture(init_calc)


def test_param(calc: RestrictedCalc):
    hp = calc['H']
    assert hp["Min"] == 0
    assert hp["Max"] == 40
    assert hp["DBE2"] == -1


def test_calc1(calc: RestrictedCalc):
    calc.setEI('N', True)
    calc.setEI('N[15]', True)
    calc.setEI('O[18]', True)
    assert set(calc.getInitedElements()) == {
        'e', 'C', 'H', 'O', 'N', 'S', 'Li', 'Na', 'K', 'F', 'Cl', 'Br', 'I', 'P', 'Si'}
    assert calc.getElements() == ['C', 'H', 'O', 'N']
    assert calc.getIsotopes() == ['N[15]', 'O[18]']
    s = ["C9H12O11N-", "C10H15O11N-", "C10H20O2N+"]
    for ss in s:
        f = Formula(ss)
        calc.clear()
        base_group = Formula('')
        base_group.charge = f.charge
        assert f in set(calc.get(f.mass(), base_group))
        g = copy.copy(f)
        g['N[15]'] = 1
        assert g in set(calc.get(g.mass(), base_group))
        g['N[15]'] = 0
        g['O[18]'] = 2
        assert g in set(calc.get(g.mass(), base_group))


def test_calc2(calc: RestrictedCalc):
    calc.setEI('H[2]', True)

    f = Formula('CH3-')
    calc.get(f.mass(), Formula('-'))
    f['H[2]'] = 2
    assert str(f) == 'CHH[2]2-'
    assert f in calc.get(f.mass(), Formula("-"))

def test_neg_dbe(calc: RestrictedCalc):
    for e in calc.getElements():
        if e not in "CHO":
            calc.setEI(e, False)

    f = Formula('C10H30')
    dbe = f.dbe()
    assert dbe == -4.0

    results = calc.get(f.mass(), base_group=Formula("H8"))
    assert f in results