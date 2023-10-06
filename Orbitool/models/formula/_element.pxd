# distutils: language = c++
# cython: language_level = 3

from libc.stdint cimport int32_t
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair

ctypedef pair[double, double] dou_pair
ctypedef pair[int32_t, int32_t] int_pair

cdef:
    # int -> element str
    list elements
    # element str -> int
    dict elementsMap
    # elementMass[elementsMap['C']] -> mass
    vector[double] elementMass
    # int -> mass num
    vector[int32_t] elementMassNum
    # int -> {mass num -> (accurate mass, relative abundance)}
    vector[unordered_map[int32_t, pair[double, double]]] elementMassDist

    int_pair str2element(str key) except *
    str element2str(int_pair&)
    
    double getMass(int_pair&)
    unordered_map[int32_t, int32_t] elementsDbe2