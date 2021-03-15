import copy
import pytest
import csv
import pathlib

from .. import Formula, RestrictedCalc


def init_calc():
    ret = RestrictedCalc()
    with pathlib.Path(__file__).parent.joinpath("element_parameters.csv").open("r") as reader:
        csvreader = iter(csv.reader(reader))
        header = next(csvreader)[1:]
        header = list(map(lambda x: x.strip(), header))
        for row in csvreader:
            ret[row[0]] = dict(zip(header, map(float, row[1:])))
    return ret

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
    assert calc.getElements() == ['C', 'H', 'O', 'N']
    assert calc.getIsotopes() == ['N[15]', 'O[18]']
    s = ["C9H12O11N-", "C10H15O11N-", "C10H20O2N+"]
    for ss in s:
        f = Formula(ss)
        calc.charge = f.charge
        calc.clear()
        assert f in set(calc.get(f.mass()))
        g = copy.copy(f)
        g['N[15]'] = 1
        assert g in set(calc.get(g.mass()))
        g['N[15]'] = 0
        g['O[18]'] = 2
        assert g in set(calc.get(g.mass()))


def test_calc2(calc: RestrictedCalc):
    calc.setEI('H[2]', True)
    calc.charge = -1

    f = Formula('CH3-')
    calc.get(f.mass())
    f['H[2]'] = 2
    assert str(f) == 'CHH[2]2-'
    assert f in calc.get(f.mass())
    