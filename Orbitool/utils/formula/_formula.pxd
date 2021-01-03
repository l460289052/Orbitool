# distutils: language = c++
# cython: language_level = 3
# distutils: language = c++
# cython: language_level = 3

from cpython cimport *
from cython.operator cimport dereference as deref, preincrement as inc
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.list cimport list as cpplist
from libcpp.unordered_map cimport unordered_map
from libcpp.unordered_set cimport unordered_set
from libcpp.map cimport map
from libcpp.pair cimport pair
from libcpp cimport bool
from libc.math cimport round, ceil, floor
import pyteomics.mass 

cdef:
    double _elements_mass(unordered_map[int, int]& elements)
    double _elements_DBE(unordered_map[int, int]& elements)
    double _elements_Omin(unordered_map[int, int]& elements)
    double _elements_Omax(unordered_map[int, int]& elements)
    double _elements_Hmin(unordered_map[int, int]& elements)
    double _elements_Hmax(unordered_map[int, int]& elements)
    bool _elements_eq(unordered_map[int, int]& elements, unordered_map[int, int]& elements)
    double _mass_isotopes_mass(double elements, cpplist[pair[int, int]]&isotopes)
    double _elements_isotopes_mass(unordered_map[int, int]&elements, cpplist[pair[int, int]]&isotopes)

    class Formula:
        cdef unordered_map[int, int] elements
        cdef cpplist[pair[int, int]] isotopes # index ->(m<<_factor) + num
        cpdef double mass(self)
        cpdef Formula findOrigin(self)
        cpdef double DBE(self)
        cdef double Omin(self)
        cdef double Omax(self)
        cdef double Hmin(self)
        cdef double Hmax(self)
        cpdef void addElement(self, str element, int m=*, int num=*) except *
        cdef void addEI(self, int index, int m, int num) except *
        @staticmethod
        cdef str eToStr(int index, int num, bool showProton)
        @staticmethod
        cdef str iToStr(int index, int m, int num)
        cpdef toStr(self, bool showProton = *, bool withCharge = *)
        cpdef double relativeAbundance(self)
        cpdef void clear(self)
        cdef void setE(self, int index, int num)except *
        cdef int getE(self, int index)
        cdef void setI(self, int index, int m, int num)except *
        cdef int getI(self, int index, int m)
        cdef Formula copy(self)
        cdef void add_(self, Formula f)except *
        cdef void sub_(self, Formula f)except *
        cdef void mul_(self, int times)except *
        cdef bool eq(self, Formula f)
        cdef bool contains(self, Formula f)




