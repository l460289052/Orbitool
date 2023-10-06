# distutils: language = c++
# cython: language_level = 3

from cython.operator cimport preincrement as preinc
from libcpp cimport bool
from libc cimport math
cimport numpy as np
import numpy as np
import cython

from ._functions cimport (DoubleArray, DoubleArray2D, DoubleArray3D, 
    DoubleOrArray)

npdouble = np.float64

cpdef tuple mergeSpectra(DoubleArray mass1, DoubleArray intensity1, 
        DoubleArray mass2, DoubleArray intensity2, double weight1,
        double weight2, double rtol, bool drop_input = False):
    cdef double total_weight = weight1+weight2
    weight1/=total_weight
    weight2/=total_weight
    if drop_input:
        intensity1*=weight1
        intensity2*=weight2
    else:
        intensity1=intensity1*weight1
        intensity2=intensity2*weight2

    cdef DoubleArray atol = rtol*np.sqrt(mass1/200)*mass1
    cdef int length1 = mass1.size, length2 = mass2.size

    cdef double[:] mass, intensity
    mass = np.empty(length1+length2,dtype=npdouble)
    intensity = np.empty(length1+length2,dtype=npdouble)

    cdef int i=0, i1=0, i2=0
    cdef double[:] m1 = mass1, m2 = mass2, int1 = intensity1, int2 = intensity2
    with cython.boundscheck(False), cython.wraparound(False):
        while i1<length1 and i2<length2:
            if math.fabs(m1[i1] - m2[i2]) <= atol[i1]:
                mass[i] = m1[i1]*weight1+m2[i2]*weight2
                intensity[i] = int1[i1]+int2[i2]
                preinc(i)
                preinc(i1)
                preinc(i2)
            elif m1[i1]<m2[i2]:
                mass[i]=m1[i1]
                intensity[i]=int1[i1]
                preinc(i)
                preinc(i1)
            else:
                mass[i]=m2[i2]
                intensity[i]=int2[i2]
                preinc(i)
                preinc(i2)
        while i1<length1:
            mass[i]=m1[i1]
            intensity[i]=int1[i1]
            preinc(i)
            preinc(i1)
        while i2<length2:
            mass[i]=m2[i2]
            intensity[i]=int2[i2]
            preinc(i)
            preinc(i2)
    return mass.base[:i], intensity.base[:i]