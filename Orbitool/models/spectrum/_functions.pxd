from libcpp cimport bool
cimport numpy as np
import numpy as np

ctypedef fused DoubleArray:
    np.ndarray[double, ndim=1]
    
ctypedef fused DoubleArray2D:
    np.ndarray[double, ndim=2]

ctypedef fused DoubleArray3D:
    np.ndarray[double, ndim=3]
    
ctypedef fused DoubleOrArray:
    double
    np.ndarray[double, ndim=1]
    
npdouble = np.float64

cpdef np.ndarray[bool, ndim=1] getPeaksPositions(DoubleArray intensity)
cpdef np.ndarray[bool, ndim=1] getNotZeroPositions(DoubleArray intensity, double min_intensity = *)