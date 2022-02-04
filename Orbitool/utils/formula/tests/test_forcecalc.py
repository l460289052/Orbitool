from .. import ForceCalc, Formula
from Orbitool.utils import formula


def test_forcecalc1():
    calc = ForceCalc()
    f = Formula('C3HO3-')
    assert f in calc.get(f.mass(), base_group=Formula("-"))

    calc['H[2]'] = 100
    calc['H'] = 0
    calc['O[18]'] = 100
    assert calc['H[2]'] == 100
    assert calc['H'] == 0
    assert calc['O[18]'] == 100
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass(), base_group=Formula("-"))


def test_forcecalc2():
    calc = ForceCalc()
    calc['H[2]'] = 100
    calc['O[18]'] = 100
    # f = Formula('C10H[2]O[18]-')
    f = Formula('C10H[2]O[18]-')
    assert f in calc.get(f.mass(), base_group=Formula("-"))


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
        ret = calc.get(f.mass(), base_group=Formula("-"))
        assert f in ret
        assert len(ret) < 25
        for r in ret:
            assert abs(r.mass() / f.mass() - 1) < calc.rtol


def test_forcecalc4():
    calc = ForceCalc()
    calc['C'] = 20
    calc['H'] = 40
    calc['C[13]'] = 3
    calc['N'] = 5
    calc['O'] = 999
    calc['O[18]'] = 3
    calc['H[2]'] = 10
    ret = calc.get(242.158, Formula("-"))
    assert Formula('C10H6H[2]10O6-') in ret


def test_forcecalc5():
    calc = ForceCalc()
    calc['N'] = 999
    f = Formula('CH4+')  # +
    assert f in calc.get(f.mass(), base_group=Formula("+"))


def test_basegroup():
    calc = ForceCalc()
    calc['N'] = 10
    calc['O'] = 10
    calc['H'] = 10
    calc['N[15]'] = 10
    calc['O[18]'] = 10
    f = Formula("HNO3")
    assert f in calc.get(f.mass(), base_group=Formula("NO3"))
    f = Formula("HNO2O[18]")
    assert f in calc.get(f.mass(), base_group=Formula("NO3"))
    f = Formula("HNO3")
    assert f in calc.get(f.mass(), base_group=Formula("HNO3"))


def test_basegroup_nonisotope():
    calc = ForceCalc()
    calc['N'] = 10
    calc['O[18]'] = 0
    calc['N[15]'] = 0
    f = Formula("HNO3")
    assert f in calc.get(f.mass())
