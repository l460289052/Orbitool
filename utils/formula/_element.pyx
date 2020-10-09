# distutils: language = c++
# cython: language_level = 3

from cython.operator cimport dereference as deref
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair
from libc.math cimport ceil, round
from pyteomics.mass import nist_mass
import numpy as np
cimport numpy as np
import re

cdef int _factor = 10
cdef int _andfactor = (1 << _factor) - 1



_pyelements = ['e', 'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O',
   'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S',
   'Cl', 'K', 'Ar', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 
   'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge',
   'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
   'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
   'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba',
   'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd',
   'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf',
   'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
   'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra',
   'Ac', 'Th', 'Pa', 'U', 'Np', 'Am', 'Am', 'Cm',
   'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf',
   'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn',
   'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og']

# min, max, DBE2, Hmin, Hmax, Omin, Omax
_pyelmentsPara = [
    ('e', [-1, 1, -1, -0.5, -0.5, 0, 0]),
    ('C', [0, 20, 2, 0, 2, 0, 3]), # H min for C is useless
    ('H', [0, 40, -1, -1, -1, 0, 0]),
    ('O', [0, 15, 0, 0, 0, -1, -1]),
    ('N', [0, 4, 1, -1, 1, 0, 3]),
    ('S', [0, 3, 0, 0, 0, 0, 4]),
    ('Li', [0, 3, -1, 0, 0, 0, 0]),
    ('Na', [0, 3, -1, 0, 0, 0, 0]),
    ('K', [0, 3, -1, 0, 0, 0, 0]),
    ('F', [0, 15, -1, -1, 0, 0, 0]),
    ('Cl', [0, 3, -1, -1, 0, 0, 3]),
    ('Br', [0, 3, -1, -1, 0, 0, 3]),
    ('I', [0, 3, -1, -1, 0, 0, 3]),
    ('P', [0, 4, 1, -1, 1, 0, 6]),
    ('Si', [0, 5, 2, 0, 2, 0, 3])]

# _pyisotopesnum = [
#     ('C[13]',3),
#     ('O[18]',2),
#     ('S[34]',1) ]

cdef list elements = list()

cdef str e
for e in _pyelements:
    elements.append(e)

# Dict[str, int]
cdef dict elementsMap = dict()

# elementMass[elementsMap['C']] -> mass
cdef vector[double] elementMass
cdef vector[int] elementMassNum
elementMass.resize(len(elements),0)
elementMassNum.resize(len(elements),0)
# elementMassDist[elementsMap['C']] -> {mass -> (accurate mass, relative abundance)}
cdef vector[unordered_map[int, pair[double, double]]] elementMassDist

cdef int i
for i, e in enumerate(elements):
    elementsMap[e] = i
    elementMassDist.push_back(unordered_map[int, pair[double, double]]())
elementsMap['e*'] = 0
elementsMap['e-'] = 0

cdef str k
cdef dict v
cdef int index
cdef tuple vv
cdef unordered_map[int, pair[double, double]] *massMap
for k, v in nist_mass.items():
    index = elementsMap.get(k, -1)
    if index == -1:
        continue
    vv = v[0]
    elementMass[index] = vv[0]
    elementMassNum[index] = <int>round(vv[0])
    massMap = &elementMassDist[index]
    for kk, vv in v.items():
        deref(massMap)[kk] = pair[double, double](vv)

cdef int CHfunc(int C):
    if C == 0:
        return 0
    elif C <= 2:
        return 4 
    elif C <= 6:
        return 6 
    elif C <= 10:
        return 8 
    elif C <= 16:
        return 10 
    elif C <= 24:
        return 12 
    elif C <= 32:
        return 14 
    elif C <= 42:
        return 16 
    elif C <= 54:
        return 18 
    else:
        return <int>ceil(0.3 * C)

cdef unordered_map[int, vector[int]] elementNumMap
cdef unordered_map[int, vector[double]] elementParasMap

def setPara(str e, list v):
    cdef int index, m
    str2element(e, &index, &m)
    if m!=0:
        raise ValueError("Can't set for isotope")
    elementNumMap[index]=v[:2]
    elementParasMap[index]=v[2:]

def getPara(str e):
    cdef int index, m
    str2element(e, &index, &m)
    cdef list para = elementNumMap[index]
    para.extend(elementParasMap[index])
    return para

def getParas():
    cdef dict ret={}
    cdef int k
    cdef list para
    for k,v in elementParasMap:
        para=elementNumMap[k]
        para.extend(v)
        ret[elements[k]]=para
    return ret

cdef list l
for k, l in _pyelmentsPara:
    setPara(k, l)
            
cdef vector[int] CHmin=[CHfunc(c) for c in range(int(elementNumMap[6][1]+1))]


cdef int encodeIsotope(int index, int m):
    return (index<<_factor)+m

cdef void decodeIsotope(int code, int*index, int*m):
    index[0] = code>>_factor
    m[0] = code&_andfactor

cdef void str2element(str key, int*index, int*m) except *:
    match = re.fullmatch(r"(e-?|[A-Z][a-z]{0,2})(\[\d+\])?", key)
    if match is None:
        raise KeyError(f'have no element {key}')
    cdef str e = match.group(1)
    index[0] = elementsMap.get(e, -1)
    if index[0] ==-1:
        raise KeyError(f'have no element {key}')
    cdef str mm = match.group(2)
    if mm is None:
        m[0] = 0
    else:
        m[0] = int(mm[1:-1])

cdef str element2str(int index, int m):
    return f"{elements[index]}[{m}]" if m>0 else f"{elements[index]}"

cdef int str2code(str key) except *:
    cdef int index, m
    str2element(key, &index, &m)
    return encodeIsotope(index, m)

cdef str code2str(int code):
    cdef int index, m
    decodeIsotope(code, &index, &m)
    return element2str(index, m)
            
# cdef unordered_map[int, int] isotopeNumMap
# cdef int m
# for k, i in _pyisotopesnum:
#     str2element(k, &index, &m)
#     isotopeNumMap[(index<<_factor)+m]=i

# def setIsoNum(str e, int v):
#     cdef int index, m
#     str2element(k, &index, &m)
#     if elementMassDist[index].find(m) == elementMassDist[index].end() or elementMassNum[index]==m:
#         raise ValueError(f'No isotope {e}')
#     index = (index<<_factor)+m
#     cdef unordered_map[int, int].iterator it = isotopeNumMap.find(index)
#     if v==0 and it!=isotopeNumMap.end():
#         isotopeNumMap.erase(it)
#     else:
#         isotopeNumMap[index]=v

# def getIsoNum(str e):
#     cdef int index, m
#     str2element(k, &index, &m)
#     index = (index<<_factor)+m
#     cdef unordered_map[int, int].iterator it = isotopeNumMap.find(index)
#     if it==isotopeNumMap.end():
#         return 0
#     return deref(it).second

# def getIsoNums():
#     cdef dict ret = dict()
#     cdef pair[int, int] it
#     for it in isotopeNumMap:
#         ret[f"{elements[it.first>>_factor]}[{it.first&_andfactor}]"]=it.second
#     return ret

del _pyelements
del _pyelmentsPara