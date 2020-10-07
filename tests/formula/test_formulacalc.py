import copy

from utils.formula import *

def test_calc1():
    calc:IonCalculatorHint = IonCalculator()
    calc.setEI('N', True)
    calc.setEI('N[15]', True)
    calc.setEI('O[18]', True)
    s = ["C9H12O11N-", "C10H15O11N-", "C10H20O2N+"]
    for ss in s:
        f:FormulaHint = Formula(ss)
        calc.charge = f.charge
        calc.clear()
        assert f in set(calc.get(f.mass()))
        g = copy.copy(f)
        g['N[15]'] = 1
        assert g in set(calc.get(g.mass()))
        g['N[15]'] = 0
        g['O[18]'] = 2
        assert g in set(calc.get(g.mass()))

def test_calc2():
    calc: IonCalculatorHint = IonCalculator()
    calc.setEI('H[2]', True)

    f = Formula('CH3-')
    calc.get(f.mass())
    f['H[2]'] = 2
    assert str(f) == 'CHH[2]2-'
    assert f in calc.get(f.mass())


def test_forcecalc1():
    calc: ForceCalculatorHint = ForceCalculator()
    f: FormulaHint = Formula('C3HO3-')
    assert f in calc.get(f.mass())

    calc.setEI('H[2]', True)
    calc.setEI('H', False)
    calc.setEI('O[18]', True)
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass())

def test_forcecalc2():
    calc: ForceCalculatorHint = ForceCalculator()
    calc.setEI('H[2]')
    calc.setEI('O[18]')
    # f = Formula('C10H[2]O[18]-')
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass())

