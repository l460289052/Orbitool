from Orbitool.utils.formula import _element

def test_():
    assert _element.py_str2element("C") == (6, 0)
    assert _element.py_str2element("C[12]") == (6, 12)