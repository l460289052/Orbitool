# distutils: language = c++
# cython: language_level = 3

from libc.stdint cimport int32_t
from libcpp.map cimport map
from libcpp.pair cimport pair

from ._element cimport int_pair
from ._formula cimport int_map, ints_pair, ints_map

cdef:
    struct State:
        int_pair isotope
        int32_t num, numMax
        double mass, massSum
    
    class Calculator:
        cdef public double rtol

        cdef map[double, pair[int32_t, int32_t]] calcedIsotopes
        cdef ints_map isotopeMaximum

        cdef void calcStateNum(self, State&state, double MR)