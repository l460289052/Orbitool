from numpy import testing as nptest
from ..nofit_func import NoFitFunc, Peak, np


def test_single_peak():
    mz = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    intensity = np.array([0, 1, 10, 1, 0], dtype=float)
    p = Peak(mz, intensity)
    func = NoFitFunc()

    fp = func.splitPeak(p, 1)[0]
    nptest.assert_approx_equal(fp.peak_position, 0.03)
    nptest.assert_approx_equal(fp.peak_intensity, 10)
    nptest.assert_approx_equal(fp.area, 0.12)

    _, int_max = func.get_peak_max([p], 0, 1)
    nptest.assert_approx_equal(int_max, 10)
    _, area_max = func.get_peak_max([p], 0, 1, "area")
    nptest.assert_approx_equal(area_max, 0.12)
    int_sum = func.get_peak_sum([p])
    nptest.assert_approx_equal(int_sum, 10)
    area_max = func.get_peak_sum([p], "area")
    nptest.assert_approx_equal(area_max, 0.12)


def test_two_peak():
    mz = np.arange(0.01, 0.12, 0.01)  # 0.01, 0.02, ..., 0.09, 0.11
    #                     1  2  3  4  5  6  7  8  9  a  b
    intensity = np.array([0, 1, 2, 3, 2, 3, 2, 3, 2, 1, 0], dtype=float)

    p = Peak(mz, intensity)
    func = NoFitFunc()

    fp1, fp2, fp3 = func.splitPeak(p, 2)

    nptest.assert_approx_equal(fp1.peak_position, 0.04)
    nptest.assert_approx_equal(fp1.peak_intensity, 3)
    nptest.assert_approx_equal(fp1.area, 0.07)
    nptest.assert_approx_equal(fp2.peak_position, 0.06)
    nptest.assert_approx_equal(fp2.peak_intensity, 3)
    nptest.assert_approx_equal(fp2.area, 0.05)
    nptest.assert_approx_equal(fp3.peak_position, 0.08)
    nptest.assert_approx_equal(fp3.peak_intensity, 3)
    nptest.assert_approx_equal(fp3.area, 0.07)

    _, int_max = func.get_peak_max([p], 0, 1)
    nptest.assert_approx_equal(int_max, 3)
    _, area_max = func.get_peak_max([p], 0, 1, "area")
    nptest.assert_approx_equal(area_max, 0.07)
    int_sum = func.get_peak_sum([p])
    nptest.assert_approx_equal(int_sum, 9)
    area_sum = func.get_peak_sum([p], "area")
    nptest.assert_approx_equal(area_sum, np.trapz(intensity, mz))
