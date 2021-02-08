import os
import pickle
import gzip
import pytest
from typing import List

import numpy as np
from numpy import testing as nptest

from Orbitool.functions.binary_search import indexNearest_np
from Orbitool.functions.spectrum import removeZeroPositions

from Orbitool.functions.spectrum import averageSpectra, getPeaksPositions

path = os.path.join(os.path.dirname(__file__), 'average_test.pickle')


@pytest.fixture
def raw_spectrums():
    return pickle.load(gzip.open(path, 'r'))


class TestSpectrum:
    def __init__(self, mass, intensity, weight) -> None:
        self.mass = mass
        self.intensity = intensity
        self.weight = weight
        self.position = getPeaksPositions(intensity)
        self.peak_mass = mass[1:-1][self.position]
        self.peak_int = intensity[1:-1][self.position]

    def find_intensities(self, peaks: List[float]):
        return np.array([self.peak_int[indexNearest_np(self.peak_mass, peak)] for peak in peaks])


def test_average(raw_spectrums):
    spectrum1, spectrum2 = [TestSpectrum(*removeZeroPositions(s[0], s[1]), s[2])
                            for s in raw_spectrums]
    w_total = spectrum1.weight + spectrum2.weight

    spectrum1_only_peaks = [545.56, 545.58, 545.80]
    spectrum2_only_peaks = [545.92, 549.85]
    both_peaks = [61.9884,255.0472]
    both_none = [123.42, 190.68]

    delta = 0.1

    mass, intensity = averageSpectra(
        [(spectrum.mass, spectrum.intensity, spectrum.weight) for spectrum in [spectrum1, spectrum2]])
    spectrum_sum = TestSpectrum(mass, intensity, 0)

    assert all(mass[1:] - mass[:-1] > 0)

    nptest.assert_array_less(spectrum_sum.find_intensities(
        spectrum1_only_peaks), spectrum1.find_intensities(spectrum1_only_peaks)*(spectrum1.weight/w_total*1.01))
    nptest.assert_array_less(spectrum_sum.find_intensities(
        spectrum2_only_peaks), spectrum2.find_intensities(spectrum2_only_peaks)*(spectrum2.weight/w_total*1.01))

    tmp_min = np.minimum(spectrum1.find_intensities(
        both_peaks), spectrum2.find_intensities(both_peaks))
    tmp_max = np.maximum(spectrum1.find_intensities(
        both_peaks), spectrum2.find_intensities(both_peaks))
    nptest.assert_array_less(
        tmp_min, spectrum_sum.find_intensities(both_peaks))
    nptest.assert_array_less(
        spectrum_sum.find_intensities(both_peaks), tmp_max)

    for peak in both_none:
        assert intensity[indexNearest_np(mass, peak)] < delta
