import OrbitoolFormulaCalc
import copy

def test_calc1():
    calc:OrbitoolFormulaCalc.IonCalculatorHint = OrbitoolFormulaCalc.IonCalculator()
    calc.setEI('N', True)
    calc.setEI('N[15]', True)
    s = ["C9H12O11N-", "C10H15O11N-", "C10H20O2N+"]
    for ss in s:
        f:OrbitoolFormulaCalc.FormulaHint = OrbitoolFormulaCalc.Formula(ss)
        calc.charge = f.charge
        calc.clear()
        assert f in set(calc.get(f.mass()))
        g = copy.copy(f)
        g['N[15]'] = 1
        assert g in set(calc.get(g.mass()))