# distutils: language = c++
# cython: language_level = 3
# distutils: language = c++
# cython: language_level = 3

from cpython cimport *
from cython.operator cimport dereference as deref, preincrement as inc
from libc.stdint cimport int32_t
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.map cimport map
from libcpp.pair cimport pair
from libcpp cimport bool
import pyteomics.mass 

ctypedef map[int32_t, int32_t] int_map
ctypedef pair[pair[int32_t, int32_t], int32_t] ints_pair
ctypedef map[pair[int32_t, int32_t], int32_t] ints_map
     

cdef:
    double _elements_mass(map[int32_t, int32_t]& elements)
    bool _elements_eq(map[int32_t, int32_t]& elements, map[int32_t, int32_t]& elements)
    double _mass_isotopes_mass(double elements, map[pair[int32_t, int32_t], int32_t]&isotopes)
    double _elements_isotopes_mass(map[int32_t, int32_t]&elements, map[pair[int32_t, int32_t], int32_t]&isotopes)

    class Formula:
        # atomic number -> number
        cdef map[int32_t, int32_t] elements
        # (atomic number, atomic mass) -> number
        # elements also contains isotopes
        cdef map[pair[int32_t, int32_t], int32_t] isotopes
        cpdef double mass(self)
        cpdef double dbe(self)except *
        cpdef Formula findOrigin(self)
        cpdef void addElement(self, str element, int32_t m=*, int32_t num=*) except *
        cdef void addEI(self, int32_t index, int32_t m, int32_t num) except *
        @staticmethod
        cdef str eToStr(int32_t index, int32_t num, bool showProton)
        @staticmethod
        cdef str iToStr(int32_t index, int32_t m, int32_t num)
        cpdef toStr(self, bool showProton = *, bool withCharge = *)
        cpdef double absoluteAbundance(self)
        cpdef double relativeAbundance(self)
        cpdef void clear(self)
        cdef void setE(self, int32_t index, int32_t num)except *
        cdef int32_t getE(self, int32_t index)
        cdef void setI(self, int32_t index, int32_t m, int32_t num)except *
        cdef int32_t getI(self, int32_t index, int32_t m)
        cdef Formula copy(self)
        cdef void add_(self, Formula f)except *
        cdef void sub_(self, Formula f)except *
        cdef void mul_(self, int32_t times)except *
        cdef bool eq(self, Formula f)
        cdef bool contains(self, Formula f)




