from numpy import array, float64 as f64
from numpy.testing import assert_almost_equal
from numpy.polynomial.polynomial import polyval
from .polynomial import polyfit_with_fixed_point


def test_fit_start_point():
    poly_coef = polyfit_with_fixed_point(
        array([1., 2]), array([-1., 0]), 2, (0, 0))
    assert abs(poly_coef[0]) < 1e-6
    assert_almost_equal([-1, 0], polyval(array([1, 2]), poly_coef), 6)


def test_fit_start_point2():
    poly_coef = polyfit_with_fixed_point(
        array([-1., 0]), array([0., -1]), 2, (1, 0))

    pred = polyval([-1, 0, 1], poly_coef)
    actual = array([0, -1, 0], dtype=f64)
    assert_almost_equal(pred, actual, 6)
