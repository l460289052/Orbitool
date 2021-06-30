import numpy as np
cimport numpy as np

cdef:
    cpdef tuple indexBetween(np.ndarray array, tuple valueRange, tuple indexRange=*)