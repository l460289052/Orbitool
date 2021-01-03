# distutils: language = c++
# cython: language_level = 3

from libc cimport math
import numpy as np
cimport numpy as np

ctypedef fused p_or_np:
    int
    float
    double
    np.ndarray[float]
    np.ndarray[double]

def maxFitNum(int num)->int:
    return <int>(math.atan((num-5)/20)*20000+4050)

def func(p_or_np mz, double a, double mu, double sigma)->double:
    return a/(math.sqrt(2*math.pi)*sigma)*np.exp(-0.5*np.power((mz-mu)/sigma,2))

def mergePeaksParam(tuple param1, tuple param2)->tuple:
    cdef double a1,a2,mu1,mu2
    a1,mu1=param1
    a2,mu2=param2
    cdef double aSum=a1+a2
    return (a1+a2,(mu1*a1+mu2*a2)/aSum)