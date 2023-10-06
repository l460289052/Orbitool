# distutils: language = c++
# cython: language_level = 3

import numpy as np
cimport numpy as np

cpdef int indexNearest(np.ndarray array, value, tuple indexRange=*)
cpdef tuple indexBetween(np.ndarray array, tuple valueRange, tuple indexRange=*)
