from .._formula import Formula
from ..functions import formula_range


def test_simple_range():
    tmp = Formula('H')
    assert list(formula_range(Formula('H10'),
                Formula('H'), Formula(), -5, 5)) == [tmp * ind for ind in range(5, 16)]


def test_minus_range():
    tmp = Formula('H')
    assert list(formula_range(Formula('H10'),
                Formula('H'), Formula(), -5, -3)) == [tmp * ind for ind in range(5, 8)]


def test_plus_range():
    tmp = Formula('H')
    assert list(formula_range(Formula('H10'),
                Formula('H'), Formula(), 3, 5)) == [tmp * ind for ind in range(13, 16)]

def test_exception_range():
    assert list(formula_range(Formula('CH4O'),
                Formula('CH2'), Formula(), -2, 2)) == list(map(Formula, ['H2O', 'CH4O', 'C2H6O', 'C3H8O']))

def test_minus_exception():
    assert list(formula_range(Formula('CH4O'),
                Formula(), Formula('CH2'), -2, 2)) == list(reversed(list(map(Formula, ['H2O', 'CH4O', 'C2H6O', 'C3H8O']))))
