# distutils: language = c++
# cython: language_level = 3

from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.list cimport list as cpplist
from libcpp.map cimport map
from libcpp.unordered_set cimport unordered_set
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair
from libcpp cimport bool
# ctypedef will cause runerror
cdef:
    double eps
    class IonCalculator:
        cdef map[double, unordered_map[int, int]] formulas
        cdef map[double, pair[double, cpplist[pair[int, int]]]] isotopes # mass -> (elements' mass, list(index, (m<<_factor) + num))
        cdef map[double, double] mcover

        cdef cpplist[int] calcedElements
        cdef cpplist[int] calcedIsotopes # (index << _factor) + m

        cdef public double ppm
        cdef public int charge
        cdef public double DBEmin
        cdef public double DBEmax
        cdef public double Mmin
        cdef public double Mmax
        cdef public bool nitrogenRule
        
        cdef bool iscovered(self, double l, double r)
        cdef void cover(self, double l, double r)
        cpdef void calc(self, double _Mmin=*, double _Mmax=*)
        cpdef clear(self)
        cdef bool getFormula(self, double& mass, map[double, unordered_map[int, int]].iterator * out)
        cdef void insertElements(self, unordered_map[int, int]& elements, double mass = *)
        cdef void insertIsotopes(self, unordered_map[int, int]& elements, double mass = *)
        cdef void insertIsotope(self, double& mass, cpplist[pair[int, int]]& isotopes)
        cdef bool getIsotope(self, double& mass, map[double, pair[double, cpplist[pair[int, int]]]].iterator *out)
