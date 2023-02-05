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
    gen.set_EI("C", 0, 20)
    gen.set_EI("H", 0, 40)
    gen.set_EI("O", 0, 15)
    gen.set_EI("N", 0, 3)
    gen.set_EI(("N", 15), 0, 1)
    gen.set_EI(("O", 18), 0, 2)
    assert gen.get_EI(("N", 0)).max == 3
    assert gen.get_EI(("N", 15)).max == 1
    calc = gen.generate()
    s = ["C9H12O11N-", "C10H15O11N-", "C10H20O2N+"]
    for ss in s:
        f = Formula(ss)
        ret = list(calc.get(f.mass(), f.charge))
        assert f in ret

        f['N[15]'] = 1
        ret = list(calc.get(f.mass(), f.charge))
        assert f in ret

        f['O[18]'] = 2
        ret = list(calc.get(f.mass(), f.charge))
        assert f in ret
