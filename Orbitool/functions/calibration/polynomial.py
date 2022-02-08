from typing import Tuple
import numpy as np


def polyfit_with_fixed_points(x: np.ndarray, y: np.ndarray, degree: int, points: np.ndarray):
    """
    from https://stackoverflow.com/questions/15191088/how-to-do-a-polynomial-fit-with-fixed-points
    """
    xf = points[:, 0]
    yf = points[:, 1]
    mat = np.empty((degree + 1 + len(xf),) * 2)
    vec = np.empty((degree + 1 + len(xf),))
    x_n = x**np.arange(2 * degree + 1)[:, None]
    yx_n = np.sum(x_n[:degree + 1] * y, axis=1)
    x_n = np.sum(x_n, axis=1)
    idx = np.arange(degree + 1) + np.arange(degree + 1)[:, None]
    mat[:degree + 1, :degree + 1] = np.take(x_n, idx)
    xf_n = xf**np.arange(degree + 1)[:, None]
    mat[:degree + 1, degree + 1:] = xf_n / 2
    mat[degree + 1:, :degree + 1] = xf_n.T
    mat[degree + 1:, degree + 1:] = 0
    vec[:degree + 1] = yx_n
    vec[degree + 1:] = yf
    params = np.linalg.solve(mat, vec)
    return params[:degree + 1]


def polyfit_with_fixed_point(x: np.ndarray, y: np.ndarray, degree: int, point: Tuple[float, float]):
    return polyfit_with_fixed_points(x, y, degree, np.array([point]))
