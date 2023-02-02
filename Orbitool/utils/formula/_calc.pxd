# distutils: language = c++
# cython: language_level = 3

from libc.stdint cimport int32_t
from libcpp.list cimport list as cpplist
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp.set cimport set
from libcpp.pair cimport pair
from libcpp cimport bool

from ._element cimport int_pair
from ._formula cimport int_map, ints_map, Formula

cdef:
    double eps
    struct State:
        int_pair isotope
        double DBE2, OMin, OMax, HMin, HMax
    