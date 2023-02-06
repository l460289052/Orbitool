from .calc import IsotopeNum, State, Calculator
from .calc_gen import CalculatorGenerator
from .. import Formula


def test_state():
    s = State(1, 1, 1, 1, 1)
    s2 = s + s
    assert s2.DBE2 == s2.HMin == s2.HMax == s2.OMin == s2.OMax == 2
    s3 = s * 4
    assert s3.DBE2 == s3.HMin == s3.HMax == s3.OMin == s3.OMax == 4
    s4 = s3 - s3
    assert s4.DBE2 == s4.HMin == s4.HMax == s4.OMin == s4.OMax == 0


def test_set():
    gen = CalculatorGenerator()
    gen.set_EI("C", 0, 20)
    gen.set_EI("H", 0, 40)
    gen.set_EI("O", 0, 15)

    assert set(gen.get_E_List()) == set("CHO")
    gen.set_EI(("C", 13), 0, 5)
    assert set(gen.get_I_of_E("C")) == {0, 13}

    gen.set_E_custom("C", True)
    gen.set_EI(("C", 12), 0, 0)
    assert set(gen.get_I_of_E("C")) == {0, 12, 13}

    assert gen.get_EI(("C", 0)).max == 20
    assert gen.get_EI(("C", 12)).max == 0
    assert gen.get_EI(("H", 0)).max == 40
    assert gen.get_EI(("O", 0)).max == 15

    gen.set_EI(("O", 18), 0, 2)
    calc = gen.generate()

    assert calc.element_nums == [
        IsotopeNum("C", 12, 13, 0, 5, 0, 20),
        IsotopeNum("O", 16, 18, 0, 2, 0, 15),
        IsotopeNum("O", 16, 16, 0, 15, 0, 15),
        IsotopeNum("H", 1, 1, 0, 40, 0, 40),
    ]


def test_restricted_1():
    """
    nitrogenrule & relative oh _ dbe & max isotope
    """
    gen = CalculatorGenerator()
    gen.nitrogenRule = True
    gen.set_EI("C", 0, 20, False)
    gen.set_EI("H", 0, 40, False)
    gen.set_EI("O", 0, 15, False)
    gen.set_EI("N", 0, 3, False)
    gen.set_EI(("N", 15), 0, 1, True)
    gen.set_EI(("O", 18), 0, 2, True)
    assert gen.get_EI(("N", 0)).max == 3
    assert gen.get_EI(("N", 15)).max == 1
    calc = gen.generate()
    calc.debug = True
    s = ["C9H12O11N-", "C10H15O11N-", "C10H20O2N+"]
    for ss in s:
        f = Formula(ss)
        ret = list(calc.get(f.mass(), f.charge))
        assert len(ret) <= 3
        assert f in ret

        f['N[15]'] = 1
        ret = list(calc.get(f.mass(), f.charge))
        assert len(ret) <= 3
        assert f in ret

        f['O[18]'] = 2
        ret = list(calc.get(f.mass(), f.charge))
        assert len(ret) <= 3
        assert f in ret


def test_restricted_2():
    gen = CalculatorGenerator()
    gen.nitrogenRule = True

    gen.del_EI("O")
    gen.set_EI("C", 0, 20, False)
    gen.set_EI("H", 0, 40, False)
    gen.set_EI(("H", 2), 0, 2, True)
    calc = gen.generate()
    f = Formula('CH3-')
    ret = list(calc.get(f.mass(), f.charge))
    assert len(ret) == 1
    assert f in ret
    f["H[2]"] = 2
    ret = list(calc.get(f.mass(), f.charge))
    assert len(ret) == 1
    assert f in ret


def test_without_oh_dbe():
    """
    neg dbe
    """
    gen = CalculatorGenerator()
    # gen.del_EI("O")
    gen.nitrogenRule = True
    gen.relativeOH_DBE = False
    calc = gen.generate()

    f = Formula('C10H30')
    dbe = f.dbe()
    assert dbe == -4.0
    ret = list(calc.get(f.mass(), 0))
    assert len(ret) <= 3
    assert f in ret

def test_any_isotope():
    gen = CalculatorGenerator()
    gen.set_EI(("H", 1), 0, 30, True) # max should be 2, 30 for comparison with below
    gen.set_EI(("H", 2), 0, 30, False)
    gen.set_EI(("O", 18), 0, 1, True)
    gen.set_EI("N", 0, 3, False)
    gen.set_EI(("N", 15), 0, 1, True)
    calc = gen.generate()

    f = Formula("C9H[2]12O11N-")
    ret = list(calc.get(f.mass(), f.charge))
    assert len(ret) == 1
    assert f in ret

    f = Formula("C9H[2]11HO11N-")
    ret = list(calc.get(f.mass(), f.charge))
    assert len(ret) == 1
    assert f in ret

def test_unlimited_isotope():
    gen = CalculatorGenerator()
    gen.set_EI(("H", 1), 0, 30, False)
    gen.set_EI(("H", 2), 0, 30, True)
    gen.set_EI(("O", 18), 0, 1, True)
    gen.set_EI("N", 0, 3, False)
    gen.set_EI("N", 0, 3, False)
    gen.set_EI(("N", 15), 0, 1, True)
    gen.maxIsotope = 20
    calc = gen.generate()

    f = Formula("C9H[2]12O11N-")
    ret = list(calc.get(f.mass(), f.charge))
    assert len(ret) > 5
    assert f in ret

    calc.relativeOH_DBE = False
    calc.nitrogenRule = False
    ret = list(calc.get(f.mass(), f.charge))
    assert len(ret) >= 20

def test_some_formula():
    gen = CalculatorGenerator()
    gen.set_EI(("O", 18), 0, 3, True)
    gen.set_EI("N", 0, 5, False)
    calc = gen.generate()

    f = Formula('C16H20O10O[18]2N3-')
    ret = list(calc.get(f.mass(), charge=f.charge))
    assert len(ret) < 3
    assert f in ret
    f = Formula('C10H17O10N3NO3-')
    ret = list(calc.get(f.mass(), charge=f.charge))
    assert len(ret) < 3
    assert f in ret

    f = Formula("HNO3")
    ret = list(calc.get(f.mass(), 0))
    assert len(ret) < 3
    assert f in ret