# distutils: language = c++
# cython: language_level = 3

from typing import Tuple
import numpy as np
cimport numpy as np
from Orbitool.functions cimport _binary_search
import cython

ctypedef np.int32_t int32
cdef fused floats:
    float
    double

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

def splitPeaks(np.ndarray[floats,ndim=1] mz, np.ndarray[floats,ndim=1] intensity)->np.ndarray:
    cdef int start = 0
    cdef int stop = len(mz)

    cdef np.ndarray[int32,ndim=1] index = np.arange(start, stop, dtype=np.int32)

    cdef double delta = 1e-6
    cdef np.ndarray[bool,ndim=1] peaksIndex = intensity > delta
    cdef np.ndarray[int32,ndim=1] l = index[:-1][peaksIndex[1:] > peaksIndex[:-1]]
    cdef np.ndarray[int32,ndim=1] r = index[1:][peaksIndex[:-1] > peaksIndex[1:]] + 1
    if len(l) < len(r):
        l = np.append((start,), l)
    elif len(l) > len(r):
        r = np.append(r, np.array((stop,)))
    return np.stack((l, r), 1)

@cython.boundscheck(False)
@cython.wraparound(False)
def safeCutSpectrum(np.ndarray[floats, ndim=1] mz, np.ndarray[floats, ndim=1] intensity, floats mzMin, floats mzMax)->Tuple[np.ndarray, np.ndarray]:
    cdef int l, r, length
    l, r = _binary_search.indexBetween(mz, (mzMin, mzMax))
    length = len(mz)
    cdef double delta = 1e-9
    while l>0 and intensity[l]>delta:
        l-=1
    if r<length and intensity[r]>delta:
        r+=1
        while r<length and intensity[r]>delta:
            r+=1
        r+=1

    if l+1<length and intensity[l+1]<delta:
        l+=1
    if r-2>0 and intensity[r-2]<delta:
        r-=1
    return mz[l:r], intensity[l:r]
    
    