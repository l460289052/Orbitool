import gzip
import pickle
import pytest
import pathlib

import numpy as np
from numpy import testing as nptest

from ....utils.formula import Formula

from ..noise import (
    denoise, denoiseWithParams, noiseLODFunc,
    getNoiseParams, getNoisePeaks)


@pytest.fixture
def mass_int():
    with gzip.open(pathlib.Path(__file__).absolute().parent.joinpath("noise_test.pickle"), 'rb') as g:
        d = pickle.load(g)
        return d["mass"], d["intensity"]


formuals = [Formula("NO3-"), Formula("HN2O6-")]
mass_points = np.fromiter((f.mass() for f in formuals), dtype=float)
mass_point_deltas = np.ones_like(mass_points, dtype=int) * 5


def test_get_param(mass_int):
    mass, intensity = mass_int
    poly, std, slt, params = getNoiseParams(
        mass, intensity, 0.5, True, mass_points, mass_point_deltas)
    nptest.assert_almost_equal(mass_points, params[:, 0, 1], 0)
    nptest.assert_almost_equal(mass_points, params[:, 1, 1], 0)


def test_denoise(mass_int):
    mass, intensity = mass_int
    poly, std, slt, param = getNoiseParams(
        mass, intensity, 0.5, True, mass_points, mass_point_deltas)
    noise, LOD = noiseLODFunc(
        mass, poly, param, mass_points, mass_point_deltas, 3)
    new_mass, new_intensity = denoiseWithParams(
        mass, intensity, poly, param, mass_points, mass_point_deltas, 3, True)

    # from matplotlib import pyplot as plt
    # plt.plot(mass, intensity, color='b')
    # plt.plot(new_mass, new_intensity, color='k')
    # plt.plot(mass, noise, color='r', linewidth=0.5)
    # plt.show()
