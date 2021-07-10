from .. import ForceCalc, Formula


def test_forcecalc1():
    calc = ForceCalc()
    f = Formula('C3HO3-')
    assert f in calc.get(f.mass())

    calc['H[2]'] = 100
    calc['H'] = 0
    calc['O[18]'] = 100
    assert calc['H[2]'] == 100
    assert calc['H'] == 0
    assert calc['O[18]'] == 100
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass())


def test_forcecalc2():
    calc = ForceCalc()
    calc['H[2]'] = 100
    calc['O[18]'] = 100
    # f = Formula('C10H[2]O[18]-')
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass())


def test_forcecalc3():
    calc = ForceCalc()
    calc['C[13]'] = 3
    calc['O[18]'] = 3
    calc['N'] = 5
    calc['H'] = 40
    calc['C'] = 40
    calc['O'] = 30

    samples = ['C16H20O10O[18]2N3-', 'C10H17O10N3NO3-']

    samples = [Formula(sample) for sample in samples]

    for f in samples:
        ret = calc.get(f.mass())
        assert f in ret
        assert len(ret) < 25
        for r in ret:
            assert abs(r.mass() / f.mass() - 1) < calc.rtol


def test_forcecalc4():
    calc = ForceCalc()  
    calc.charge = 1
    calc['N'] = 999
    f = Formula('CH4+')  # +
    assert f in calc.get(f.mass())
