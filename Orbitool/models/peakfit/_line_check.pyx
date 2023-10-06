# distutils: language = c++
# cython: language_level = 3

import numpy as np
from libcpp cimport bool
cimport numpy as np
import cython

ctypedef fused floats:
    float
    double

from Orbitool.utils.binary_search._binary_search cimport indexBetween

cdef cross(floats x1, floats y1, floats x2, floats y2):
    return x1*y2-x2*y1

cdef checkCrossed(floats l1x1,floats l1y1,floats l1x2,floats l1y2,floats l2x1,floats l2y1,floats l2x2,floats l2y2):
    cdef bool c1, c2
    c1 = (cross(l1x2-l1x1,l1y2-l1y1,l2x1-l1x1,l2y1-l1y1)>0)^(cross(l1x2-l1x1,l1y2-l1y1,l2x2-l1x1,l2y2-l1y1)>0)
    c2 = (cross(l2x2-l2x1,l2y2-l2y1,l1x1-l2x1,l1y1-l2y1)>0)^(cross(l2x2-l2x1,l2y2-l2y1,l1x2-l2x1,l1y2-l2y1)>0)
    return c1 and c2

@cython.boundscheck(False)
@cython.wraparound(False)
def linePeakCrossed(tuple line, floats[:] mz, floats[:] intensity)->bool:
    cdef floats x1,y1,x2,y2
    if line[0][0]<line[1][0]:
        x1, y1 = line[0]
        x2, y2 = line[1]
    else:
        x1, y1 = line[1]
        x2, y2 = line[0]

    cdef int start, stop, index
    start, stop = indexBetween(mz.base, (x1, x2))
    start = (start - 1) if start > 0 else 0
    if stop >= len(mz):
        stop = len(mz) - 1

    cdef bool c1, c2
    for index in range(start, stop):
        if checkCrossed(x1,y1,x2,y2,mz[index],intensity[index],mz[index+1],intensity[index+1]):
            return True
    return False