import pytest
from utils.convert_formula import *


def test_convert_to_dict():
    f = "(H2O)3NO3-"
    d = convert_to_dict(f)
    assert d == {
        'H': 6,
        'O': 6,
        'N': 1,
        'charge': -1}

    assert convert_to_dict(convert_from_dict(
        convert_to_dict(f))) == convert_to_dict(f)

    f = "(((HAbc2)2)2O)2"
    assert convert_to_dict(f) == {'H': 8, 'Abc': 16, 'O': 2}

    f = "((H2O)3(NO3)3)2-"
    assert convert_to_dict(f) == {'H': 12, 'O': 24, 'N': 6, 'charge': -1}


def test_error():
    f = "(H2O3NO3-"
    with pytest.raises(ValueError):
        convert_to_dict(f)
