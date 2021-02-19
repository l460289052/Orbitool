# distutils: language = c++
# cython: language_level = 3

from cython.operator cimport dereference as deref
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair
from libc.math cimport round
from pyteomics.mass import nist_mass
import re

cdef list elements = [
   'e', 'H', 'He',
   'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
   'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
   'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
   'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe',
   'Cs', 'Ba',
       'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',
       'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn',
   'Fr', 'Ra',
       'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr',
       'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og']

# Dict[str, int]
cdef dict elementsMap = dict()

# elementMass[elementsMap['C']] -> mass
cdef vector[double] elementMass
cdef vector[int32_t] elementMassNum
elementMass.resize(len(elements),0)
elementMassNum.resize(len(elements),0)
# elementMassDist[elementsMap['C']] -> {mass -> (accurate mass, relative abundance)}
cdef vector[unordered_map[int32_t, dou_pair]] elementMassDist

cdef int32_t i
cdef str e
for i, e in enumerate(elements):
    elementsMap[e] = i
    elementMassDist.push_back(unordered_map[int32_t, pair[double, double]]())
elementsMap['e*'] = 0
elementsMap['e-'] = 0

cdef dict v
cdef int32_t index
cdef tuple vv
cdef vector[unordered_map[int32_t, dou_pair]].iterator massMap
for e, v in nist_mass.items():
    index = elementsMap.get(e, -1)
    if index == -1:
        continue
    vv = v[0]
    elementMass[index] = vv[0]
    elementMassNum[index] = <int32_t>round(vv[0])
    massMap = elementMassDist.begin() + index
    for kk, vv in v.items():
        deref(massMap)[kk] = dou_pair(vv)


cdef int_pair str2element(str key) except *:
    cdef int32_t m, index
    match = re.fullmatch(r"(e-?|[A-Z][a-z]{0,2})(\[\d+\])?", key)
    if match is None:
        raise KeyError(f'have no element {key}')
    cdef str e = match.group(1)
    index = elementsMap.get(e, -1)
    if index ==-1:
        raise KeyError(f'have no element {key}')
    cdef str mm = match.group(2)
    if mm is None:
        m = 0
    else:
        m = int(mm[1:-1])
    return int_pair(index, m)

cdef str element2str(int_pair& element):
    return f"{elements[element.first]}[{element.second}]" if element.second>0 else f"{elements[element.first]}"

def py_str2element(str key):
    cdef int_pair ret = str2element(key)
    return ret.first, ret.second
    
def py_element2str(int32_t index, int32_t m):
    return element2str(int_pair(index, m))

cdef double getMass(int_pair& p):
    return elementMassDist[p.first][p.second].first