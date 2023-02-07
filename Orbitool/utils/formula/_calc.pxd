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
        double DBE2, OMin, OMax, HMin, HMax
    struct NumState:
        int32_t e, current, e_current, max, global_limit_sum
        double mass
    struct IsotopeNum:
        int32_t e, i_num, i_min, i_max, e_min, e_max
        bool global_limit
    class Calculator:
        cdef double rtol, DBEMin, DBEMax, H_max_mass
        cdef int32_t global_limit
        cdef bool nitrogen_rule, dbe_limit
        cdef map[int32_t, State] element_states
        cdef vector[IsotopeNum] element_nums

        cpdef bool check(self, Formula f, double ml, double mr, double charge)
