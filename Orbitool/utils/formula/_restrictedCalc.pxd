# distutils: language = c++
# cython: lanuage_level = 3

from libc.stdint cimport int32_t
from libcpp.list cimport list as cpplist
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp.set cimport set
from libcpp.pair cimport pair
from libcpp cimport bool

from ._formula cimport int_map, ints_map, Formula

ctypedef map[double, map[int32_t, int32_t]] d_ii_map_map
ctypedef pair[double, map[int32_t, int32_t]] d_ii_map_pair
ctypedef pair[double, map[pair[int32_t, int32_t], int32_t]] d_ii_i_map_pair
ctypedef map[double, pair[double, map[pair[int32_t, int32_t], int32_t]]] d_d_ii_i_map_pair_map
ctypedef pair[double, pair[double, map[pair[int32_t, int32_t], int32_t]]] d_d_ii_i_map_pair_pair

cdef:
    double eps
    
    struct State:
        double DBE2, OMin, OMax, HMin, HMax

    class Calculator:
        cdef public double rtol

        cdef map[double, map[int32_t, int32_t]] formulas
        # isotopes -> (formulas mass, Dict[(index, m) -> num])
        cdef map[double, pair[double, map[pair[int32_t, int32_t], int32_t]]] isotopes
        cdef map[double, double] mCover

        cdef cpplist[int32_t] calcedElements
        cdef cpplist[pair[int32_t, int32_t]] calcedIsotopes

        cdef public double DBEMin
        cdef public double DBEMax
        cdef public double MMin
        cdef public double MMax
        cdef public bool nitrogenRule
        
        cdef vector[int32_t] ElementNumMin
        cdef vector[int32_t] ElementNumMax
        cdef vector[double] ElementDbe2
        cdef vector[double] ElementHMin
        cdef vector[double] ElementHMax
        cdef vector[double] ElementOMin
        cdef vector[double] ElementOMax
        cdef vector[State] ElementState
        cdef vector[bool] ElementInited
        
        cdef double OMin(self, int_map& elements)
        cdef double OMax(self, int_map& elements)
        cdef double HMin(self, int_map& elements)
        cdef double HMax(self, int_map& elements)
        cdef double DBE(self, int_map& elements)
        
        cdef bool isCovered(self, double l, double r)
        cdef void cover(self, double l, double r)
        
        cdef int32_t checkParameters(self)
        
        cdef setStateForFormula(self, State&state, int_map&elements)

        cpdef void calc(self, Formula base_group, double MMin=*, double MMax=*)except*
        cpdef clear(self)
        cdef pair[bool, map[double, map[int32_t, int32_t]].iterator] getFormula(self, double&mass)
        cdef void insertElements(self, int_map&elements, double mass=*)
        cdef void insertIsotopes(self, int_map&elements, double mass=*)
        cdef void insertIsotope(self, double&mass, ints_map&isotopes)
        cdef pair[bool, map[double, pair[double, map[pair[int32_t, int32_t], int32_t]]].iterator] getIsotope(self, double&mass)
        