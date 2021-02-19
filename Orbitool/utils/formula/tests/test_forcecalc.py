def test_forcecalc1():
    calc: ForceCalculatorHint = ForceCalculator()
    f: FormulaHint = Formula('C3HO3-')
    assert f in calc.get(f.mass())

    calc['H[2]'] = 100
    calc['H'] = 0
    calc['O[18]'] = 100
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass())

def test_forcecalc2():
    calc: ForceCalculatorHint = ForceCalculator()
    calc['H[2]'] = 100
    calc['O[18]'] = 100
    # f = Formula('C10H[2]O[18]-')
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass())


def test_forcecalc3():
    calc: ForceCalculatorHint = ForceCalculator()
    calc['C[13]'] = 3
    calc['O[18]'] = 3
    calc['N'] = 5
    calc['H'] = 40
    calc['C'] = 40
    calc['O'] = 30

    samples = ['C16H20O10O[18]2N3-','C10H17O10N3NO3-']

    samples = [Formula(sample) for sample in samples]

    for f in samples:
        ret = calc.get(f.mass())
        assert f in ret
        assert len(ret) < 25
