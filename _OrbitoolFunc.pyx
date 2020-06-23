# distutils: language = c++
# cython: language_level = 3


# from cython.parallel import prange
from libc cimport math
from libcpp cimport bool
import numpy as np
cimport numpy as np
import cython

ctypedef np.uint8_t uint8
ctypedef np.int32_t int32
ctypedef np.int64_t int64

ctypedef fused floats:
    float
    double

def indexNearest(np.ndarray array, value, tuple indexRange = None) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    cdef int l, r
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = np.searchsorted(array[l:r], value) + l
    if i == r or i > 0 and abs(array[i-1]-value) < abs(array[i]-value):
        return i-1
    else:
        return i

def indexBetween(np.ndarray array, tuple valueRange, tuple indexRange = None) -> (int, int):
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



def getPeaks(np.ndarray[floats,ndim=1] mz, np.ndarray[floats,ndim=1] intensity, tuple indexRange, tuple mzRange)->np.ndarray:
    cdef int start = 0
    cdef int stop = len(mz)
    if indexRange is not None:
        start, stop = indexRange
    elif mzRange is not None:
        start, stop = indexBetween(mz, mzRange)

    mz = mz[start:stop]
    intensity = intensity[start:stop]
    cdef np.ndarray[int32,ndim=1] index = np.arange(start, stop, dtype=np.int32)

    cdef double delta = 1e-6
    cdef np.ndarray[uint8,ndim=1] peaksIndex = intensity > delta
    cdef np.ndarray[int32,ndim=1] l = index[:-1][peaksIndex[1:] > peaksIndex[:-1]]
    cdef np.ndarray[int32,ndim=1] r = index[1:][peaksIndex[:-1] > peaksIndex[1:]] + 1
    if l[0] + 1 >= r[0]:
        l = np.append((start,), l)
    if l[-1] + 1 >= r[-1]:
        r = np.append(r, np.array((stop,)))
    return np.stack((l, r), 1)

def peakAt(np.ndarray[floats,ndim=1] intensity)->np.ndarray:
    cdef np.ndarray[uint8,ndim=1] peak = intensity[:-1] < intensity[1:]
    peak = peak[:-1] > peak[1:]
    return peak

def getNoise(np.ndarray[floats,ndim=1] mz, np.ndarray[floats,ndim=1] intensity, floats quantile):
    cdef np.ndarray[uint8,ndim=1] peak = peakAt(intensity)
    mz = mz[1:-1][peak]
    intensity = intensity[1:-1][peak]

    cdef double l = 0.5
    cdef double r = 0.8
    cdef np.ndarray[floats,ndim=1] tmp = mz - np.floor(mz)
    cdef np.ndarray[np.uint8_t,ndim=1] select = (tmp > l) & (tmp < r)
    mz = mz[select]
    intensity = intensity[select]

    # noise
    select = intensity < (intensity.mean() + intensity.std() * 3)
    mz = mz[select]
    intensity = intensity[select]
    cdef double noiseQuantile = np.quantile(intensity, quantile)
    cdef double noiseStd = np.std(intensity)

    return peak, (mz, intensity), (noiseQuantile, noiseStd)

@cython.boundscheck(False)
def denoiseWithLOD(np.ndarray[floats,ndim=1] mz,np.ndarray[floats] intensity, tuple LOD, np.ndarray[np.uint8_t,ndim=1] peak, bool minus=True):
    cdef int length = len(mz)
    cdef np.ndarray[floats,ndim=1] newIntensity = np.zeros_like(intensity)
    cdef double mean = LOD[0]
    cdef double std = LOD[1]
    cdef double MAX = mean + 3 * std

    # len = len(peak)
    cdef np.ndarray[int32,ndim=1] peakmzIndex = np.arange(0, length,dtype=np.int32)[1:-1][peak]
    # peakMz = mz[1:-1][peak]
    cdef np.ndarray[floats,ndim=1] peakIntensity = intensity[1:-1][peak]

    cdef np.ndarray[int64,ndim=1] arg = peakIntensity.argsort()
    peakmzIndex = peakmzIndex[arg]
    peakIntensity = peakIntensity[arg]

    cdef int thresholdIndex = np.searchsorted(peakIntensity, MAX, 'right')
    peakmzIndex = peakmzIndex[thresholdIndex:]
    cdef int i, mzIndex, l, r
    cdef double peakI
    # for i in prange(len(peakmzIndex)):
    for i in range(len(peakmzIndex)):
        mzIndex = peakmzIndex[i]
        l = mzIndex - 1
        r = mzIndex + 1
        while l > 0 and intensity[l] > intensity[l - 1]:
            l -= 1
        while r < length and intensity[r] > intensity[r + 1]:
            r += 1
        if minus:
            peakI = intensity[mzIndex]
            newIntensity[l:r + 1] = intensity[l:r + 1] / peakI * (peakI - mean)
        else:
            newIntensity[l:r + 1] = intensity[l:r + 1]

    cdef double delta = 1e-6
    cdef np.ndarray[uint8,ndim=1] select = newIntensity > delta
    # select[1:] = select[1:] | select[:-1]
    # select[:-1] = select[:-1] | select[1:]
    select[1:] |= select[:-1]
    select[:-1] |= select[1:]
    mz = mz[select]
    newIntensity = newIntensity[select]
    return mz, newIntensity

def linePeakCrossed(tuple line, np.ndarray[floats,ndim=1] mz, np.ndarray[floats,ndim=1] intensity)->bool:
    cdef np.ndarray[floats,ndim=1] p1
    cdef np.ndarray[floats,ndim=1] p2
    if line[0][0]<line[1][0]:
        p1=np.array(line[0])
        p2=np.array(line[1])
    else:
        p1=np.array(line[1])
        p2=np.array(line[0])
    cdef int start, stop, index
    start, stop = indexBetween(mz, (p1[0], p2[0]))
    start = (start - 1) if start > 0 else 0
    if stop >= len(mz):
        stop = len(mz) - 1
    cdef np.ndarray[floats,ndim=1] l, p3, p4
    cdef np.ndarray[floats,ndim=2] tmp
    cdef bool c1, c2
    for index in range(start, stop):
        tmp = np.stack((mz[index:index + 2],
                        intensity[index:index + 2]), axis=1)
        p3 = tmp[0]
        p4 = tmp[1]
        l = p2 - p1
        c1 = (np.cross(l, p3 - p1) >
              0) ^ (np.cross(l, p4 - p1) > 0)
        l = p4 - p3
        c2 = (np.cross(l, p1 - p3) >
              0) ^ (np.cross(l, p2 - p3) > 0)
        if c1 and c2:
            return True
    return False

ctypedef fused p_or_np:
    int
    float
    double
    np.ndarray[float]
    np.ndarray[double]

class NormalDistributionFunc:
    @staticmethod
    def maxFitNum(int num)->int:
        return <int>(math.atan((num-5)/20)*20000+4050)

    @staticmethod
    def _func(p_or_np mz, double a, double mu, double sigma)->double:
        return a/(math.sqrt(2*math.pi)*sigma)*np.exp(-0.5*np.power((mz-mu)/sigma,2))

    @staticmethod
    def mergePeaksParam(tuple param1, tuple param2)->tuple:
        cdef double a1,a2,mu1,mu2
        a1,mu1=param1
        a2,mu2=param2
        cdef double aSum=a1+a2
        return (a1+a2,(mu1*a1+mu2*a2)/aSum)
