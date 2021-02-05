# distutils: language = c++
# cython: language_level = 3

import numpy as np
cimport numpy as np

cpdef np.ndarray[bool, ndim=1] getPeaksPositions(DoubleArray intensity):
    """
    need remove zeros before get peaks position
    """
    cdef np.ndarray[bool, ndim=1] positions = intensity[:-1]<intensity[1:]
    positions=positions[:-1]>positions[1:]
    return positions

cpdef np.ndarray[bool, ndim=1] getNotZeroPositions(DoubleArray intensity, double min_intensity = 1e-6):
    cdef np.ndarray[bool, ndim=1] slt = intensity > min_intensity
    slt[1:]|=slt[:-1]
    slt[:-1]|=slt[1:]
    return slt