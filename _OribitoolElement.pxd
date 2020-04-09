# distutils: language = c++
# cython: language_level = 3

from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair

cdef:
    int _factor
    int _andfactor
    void str2element(str key, int*index, int*m) except *

    list elements
    dict elementsMap
    # elementMass[elementsMap['C']] -> mass
    vector[double] elementMass
    vector[int] elementMassNum
    # elementMassDist[elementsMap['C']] -> {mass -> (accurate mass, relative abundance)}
    vector[unordered_map[int, pair[double, double]]] elementMassDist
    # min, max
    unordered_map[int, vector[int]] elementNumMap
    # dbe2, hmin, hmax, omin, omax
    unordered_map[int, vector[double]] elementParasMap
    vector[int] CHmin

    # unordered_map[int, int] isotopeNumMap