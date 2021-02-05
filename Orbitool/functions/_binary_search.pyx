# distutils: language = c++
# cython: language_level = 3
import numpy as np
cimport numpy as np
import cython

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef int indexNearest(np.ndarray array, value, tuple indexRange = None):
    '''
    `indexRange`: default=(0,len(array))
    '''
    cdef int i, l, r
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = np.searchsorted(array[l:r], value) + l
    if i == r or i > 0 and np.abs(array[i-1]-value) < np.abs(array[i]-value):
        return i-1
    else:
        return i

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef tuple indexBetween(np.ndarray array, tuple valueRange, tuple indexRange = None):
    cdef int ll,rr,l,r
    ll, rr = (0, len(array)) if indexRange is None else indexRange
    lvalue, rvalue = valueRange
    array = array[ll:rr]
    l = np.searchsorted(array, lvalue) + ll
    r = np.searchsorted(array, rvalue, 'right') + ll
    if l < r:
        return (l, r)
    else:
        return (l, l)
