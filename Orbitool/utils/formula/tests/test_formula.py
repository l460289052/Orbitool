import threading
from copy import copy

import pytest
from pyteomics import mass as pyteomass

from .. import Formula


def test_formula1():
    s = "N[15]O3-"
    f = Formula(s)
    assert f['O'] == 3
    assert f['N[15]'] == 1
    assert f['N'] == 1
    assert f.charge == -1
    assert f.dbe() == 1.
    assert len(f) == 3
    assert dict(f.items()) == {
        "N[15]": 1,
        "O": 3,
        "e": 1}
    assert f.atoms() == Formula("NO-")


def formula2():
    'O[18]3O0C7H[2]0H2'
    f = Formula()
    f.addElement('O', 18, 3)
    f.addElement('O', 0, 0)
    f.addElement('C', 0, 7)
    f.addElement('H', 2, 0)
    f.addElement('H', 0, 2)


def test_formula2():
    '''
    用thread不顶用的，大家都在等这个线程退出，我也不知道它该怎么退出，唉
    '''
    thread = threading.Thread(target=formula2)
    thread.start()
    thread.join(timeout=0.1)
    assert not thread.is_alive()
    thread._stop()
    del thread


def test_mass():
    f = Formula("CH4-")
    e = Formula(charge=-1)
    assert len(f) == 3
    assert (
        f.mass() - pyteomass.calculate_mass(f.toStr(withCharge=False)) - e.mass()) < 1e-6


def test_isotopes():
    f = Formula("C[14]2")
    assert str(f) == "C[14]2"

    c = Formula("C")
    c14 = Formula("C[14]")
    g = copy(f)
    f["C[14]"] = 1
    assert f["C[14]"] == 1
    assert f["C"] == 2
    assert f["C[12]"] == 1
    assert str(f) == "CC[14]"
    h = g - c14 + c
    assert h["C[14]"] == 1
    assert h["C"] == 2
    assert h["C[12]"] == 1
    assert h.mass() == f.mass()
    assert (h.to_numpy() == f.to_numpy()).all()
    assert h == f

    assert Formula.from_numpy(f.to_numpy()) == f

    assert g.findOrigin() == f.findOrigin()
    assert g.atoms() == f.atoms() == Formula("C")


def test_to_dict():
    f = Formula("C10H17O10N3NO3-")
    assert f.to_dict() == {
        "C": 10,
        "H": 17,
        "O": 13,
        "N": 4,
        "e": 1}
    assert Formula(f.to_dict()) == f

    f = Formula("C16H20O10O[18]2N3-")
    assert f.to_dict() == {
        "C": 16,
        "H": 20,
        "O": 10,
        "N": 3,
        "O[18]": 2,
        "e": 1}
    assert Formula(f.to_dict()) == f


def test_recurrent():
    f = Formula("(C2(C2(C2H4O[18])2)2e-2)2")
    assert f['C'] == 28
    assert f['H'] == 32
    assert f['O[18]'] == 8
    assert f.charge == -4


def test_recurrent_error():
    with pytest.raises(ValueError):
        f = Formula("((C)))")


def test_lower():
    f = Formula("c2h5-2")
    assert f['C'] == 2
    assert f['H'] == 5
    assert f.charge == -2
    assert f == Formula("C2H5e-2")


def test_upper():
    f = Formula("CuE+2")
    assert f == Formula("Cu+2")
    g = Formula("Cu")
    g.charge = 2
    assert f == g


def test_space():
    f = Formula("c 25 h 36")
    assert f['C'] == 25
    assert f['H'] == 36

def test_atoms():
    f = Formula("SO4-2")
    assert f.atoms() == Formula("SO-")