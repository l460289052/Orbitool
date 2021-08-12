# distutils: language = c++
# cython: language_level = 3
from cpython cimport *
from cython.operator cimport dereference as deref, preincrement as inc
from libc.stdint cimport int32_t, uint64_t
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.list cimport list as cpplist
from libcpp.unordered_set cimport unordered_set
from libcpp.map cimport map
from libcpp.pair cimport pair
from libcpp cimport bool
from libc.math cimport round, ceil, floor
import pyteomics.mass 
import re
from typing import Union

import cython
import numpy as np
cimport numpy as np

from ._element cimport elements, elementsMap, elementMass,\
     elementMassNum, elementMassDist, str2element, element2str,\
     elementsDbe2

from ._element cimport dou_pair, int_pair

cdef int32_t hash_factor = 10

cdef list _elementsOrder = ['C', 'H', 'O', 'N', 'S']

cdef vector[int32_t] elementsOrder = [elementsMap[e] for e in _elementsOrder]
cdef unordered_set[int32_t] elementsOrderSet = unordered_set[int32_t]()
elementsOrderSet.insert(elementsOrder.begin(), elementsOrder.end())


cdef double _elements_mass(int_map & elements):
    cdef double mass = 0
    cdef int_pair i
    for i in elements:
        mass+=elementMass[i.first]*i.second
    return mass

cdef bool _elements_eq(int_map&_f1, int_map&_f2):
    if _f1.size()!=_f2.size():
        return False
    i1 = _f1.begin()
    i2 = _f2.begin()
    while i1 != _f1.end():
        if deref(i1) != deref(i2):
            return False
        inc(i1)
        inc(i2)

    return True

cdef double _mass_isotopes_mass(double mass, ints_map&isotopes):
    cdef ints_pair i
    for i in isotopes:
        mass+=i.second*(elementMassDist[i.first.first][i.first.second].first-elementMass[i.first.first])
    return mass

cdef double _elements_isotopes_mass(int_map&elements, ints_map&isotopes):
    return _mass_isotopes_mass(_elements_mass(elements), isotopes)
    

cdef class Formula:
    def __init__(self, formula : Union[str, dict] = None, **kwargs):
        '''
        Formula('CC[13]H5O-')
        Formula({'C':1,'C[13]':1,'H':5,'O':1},charge=-1)
        Formula({'C':1,'C[13]':1,'H':5,'O':1,'charge'=-1})
        Formula(C=1,H=2,O=1,charge=-1)
        '''
        cdef str charge, e, m_str, num, k
        cdef int32_t m_int
        cdef int32_t v
        cdef dict dic
        try:
            if isinstance(formula, str):
                formula = formula.strip()
                if not re.fullmatch(r"([A-Z][a-z]{0,2}(\[\d+\])?\d*)*[-+]?", formula):
                    raise ValueError(str(formula))
                if len(formula) > 0:
                    charge = formula[-1]
                    if charge == '+':
                        self.setE(0,-1)
                    elif charge == '-':
                        self.setE(0,1)
                for match in re.finditer(r"([A-Z][a-z]{0,2})(\[\d+\])?(\d*)", formula):
                    e = match.group(1)
                    m_str = match.group(2)
                    if m_str is None:
                        m_int = 0
                    else:
                        m_int = int(m_str[1:-1])
                    num = match.group(3)
                    if len(num) == 0:
                        self.addElement(e, m_int)
                    else:
                        self.addElement(e, m_int, int(num))
            else:
                dic = kwargs
                if isinstance(formula, dict):
                    dic.update(formula)
                for k, v in dic.items():
                    match = re.fullmatch(r"([A-Z][a-z]{0,2})(\[\d+\])?", k)
                    if match is not None:
                        e = match.group(1)
                        m_str = match.group(2)
                        if m_str is None:
                            m_int = 0
                        else:
                            m_int = int(m_str[1:-1])
                        self.addElement(e, m_int, v)
                    elif k == 'charge':
                        self.setE(0,-v)
                    elif k.startswith('e'):
                        self.setE(0,v)
                    else:
                        raise ValueError('wrong kwargs'+k)
        except ValueError as e:
            raise ValueError('wrong formula:' + str(e))
        
    property charge:
        def __get__(self):
            return -self.getE(0)

        def __set__(self, int32_t value):
            self.setE(0, -value)
            
    @property
    def isIsotope(self):
        return self.isotopes.size() > 0

    cpdef double mass(self):
        return _elements_isotopes_mass(self.elements, self.isotopes)

    cpdef double dbe(self) except*:
        cdef int_pair e
        cdef double dbe = 2
        for e in self.elements:
            it = elementsDbe2.find(e.first)
            if it == elementsDbe2.end():
                raise ValueError(f"Please set DBE for '{elements[e]}'")
            dbe += e.second * deref(it).second
        return dbe / 2

    cpdef Formula findOrigin(self):
        cdef Formula formula = Formula.__new__(Formula)
        formula.elements = self.elements
        return formula

    cpdef void addElement(self, str element, int32_t m = 0, int32_t num=1) except *:
        cdef int32_t index = elementsMap.get(element, -1)
        if index == -1:
            raise ValueError(f'unknown element:{element}')
        self.addEI(index, m, num)


    cdef void addEI(self, int32_t index, int32_t m, int32_t num) except *:
        # if num == 0:
        #     return
        if m > 0:
            if elementMassDist[index].find(m) == elementMassDist[index].end():
                raise ValueError(f'unknown element:{elements[index]}[{m}]')
            self.setE(index, self.getE(index) + num)
            if elementMassNum[index] != m:  # isotope
                self.setI(index, m, self.getI(index, m) + num)
        else:
            self.setE(index, self.getE(index) + num)

    @staticmethod
    cdef str eToStr(int32_t index, int32_t num, bool showProton):
        cdef str e= f"{elements[index]}[{elementMassNum[index]}]" if showProton else elements[index]
        if num==1:
            return e
        elif num>1:
            return e+str(num)
        else:
            return ''
    @staticmethod
    cdef str iToStr(int32_t index, int32_t m, int32_t num):
        if num==1:
            return f"{elements[index]}[{m}]"
        elif num>1:
            return f"{elements[index]}[{m}]{num}"
        else:
            return ''

    cpdef toStr(self, bool showProton = False, bool withCharge = True):
        cdef list rets=[]

        cdef int_pair p, e
        cdef int32_t i, index, num
        for i in elementsOrder:
            it = self.elements.find(i)
            if it != self.elements.end():
                index = deref(it).first
                num = deref(it).second
                p = int_pair(index, 0)
                isoit = self.isotopes.upper_bound(p)
                inc(p.first)
                isoend = self.isotopes.upper_bound(p)
                rets.append(Formula.eToStr(index,num - self.getI(index,0), showProton))
                while isoit != isoend:
                    rets.append(Formula.iToStr(index,deref(isoit).first.second,deref(isoit).second))
                    inc(isoit)

        for e in self.elements:
            index=e.first
            if index > 0:
                num=e.second
                if elementsOrderSet.find(index) == elementsOrderSet.end():
                    p = int_pair(index, 0)
                    isoit = self.isotopes.upper_bound(p)
                    inc(p.first)
                    isoend = self.isotopes.upper_bound(p)
                    rets.append(Formula.eToStr(index, num-self.getI(index,0), showProton))
                    while isoit!=isoend:
                        rets.append(Formula.iToStr(index ,deref(isoit).first.second, deref(isoit).second))
                        inc(isoit)
                  
        if withCharge:
            index = self.getE(0)
            if index==1:
                return ''.join(rets) +'-'
            elif index==-1:
                return ''.join(rets) +'+'
            elif index > 0:
                return ''.join(rets)+ f'e-{index}'
            elif index < 0:
                return ''.join(rets)+ f'e+{-index}'
        return ''.join(rets)

    cpdef double absoluteAbundance(self):
        return pyteomics.mass.isotopic_composition_abundance(formula=self.toStr(True, False))

    cpdef double relativeAbundance(self):
        if not self.isIsotope:
            return 1
        return pyteomics.mass.isotopic_composition_abundance(formula=self.toStr(True, False)) /\
            pyteomics.mass.isotopic_composition_abundance(
                formula=self.findOrigin().toStr(True, False))

    cpdef void clear(self):
        self.elements.clear()
        self.isotopes.clear()

    cdef void setE(self, int32_t index, int32_t num) except *:
        if index != 0 and num<self.getI(index,0):
            raise ValueError(f"the number of {index} '{elements[index]}' shouldn't be lesser than {self.getI(index,0)}")
        
        it = self.elements.find(index)
        
        if it == self.elements.end():
            if num != 0:
                self.elements[index] = num
        else:
            if num == 0:
                self.elements.erase(it)
            else:
                deref(it).second = num

    cdef int32_t getE(self, int32_t index):
        '''
        contains isotopes
        '''
        it = self.elements.find(index)
        if it == self.elements.end():
            return 0
        return deref(it).second

    cdef void setI(self, int32_t index, int32_t m, int32_t num) except *:
        '''
        wouldn't change elements' nums
        eg. C2 -> setI(6,13,1) -> CC[13]
            spectial: setI(6,0,0) # clear
        '''
        if num<0:
            raise ValueError(f"the number of {index} '{elements[index]}[{m}]' shouldn't be lesser than 0")
        cdef int_pair p = int_pair(index, m)
        if num==0:
            if m==0:
                it = self.isotopes.upper_bound(p)
                inc(p.first)
                end = self.isotopes.upper_bound(p)
                self.isotopes.erase(it, end)
            else:
                it = self.isotopes.find(p)
                if it!=self.isotopes.end():
                    self.isotopes.erase(it)
        else:
            if m==0:
                raise ValueError("if m==0, index must equal to 0")
            if self.getE(index)<self.getI(index,0)-self.getI(index,m)+num:
                raise ValueError(f"the number of {index} '{elements[index]}[{m}]' shouldn't be greater than {self.getE(index)-self.getI(index,0)+self.getI(index,m)}")
            it = self.isotopes.find(p)
            if it!=self.isotopes.end():
                deref(it).second = num
            else:
                self.isotopes[p] = num

    cdef int32_t getI(self, int32_t index, int32_t m):
        '''
        CC[13]C[14] -> getI(6,m = 0) -> 2
        '''
        cdef int_pair p = int_pair(index, m)
        cdef int32_t ret = 0
        if m != 0:
            i = self.isotopes.find(p)
            if i == self.isotopes.end():
                return 0
            return deref(i).second
        else:
            i = self.isotopes.upper_bound(p)
            inc(p.first)
            end = self.isotopes.upper_bound(p)
            while i!=end:
                ret += deref(i).second
                inc(i)
            return ret

    cdef Formula copy(self):
        cdef Formula ret = Formula.__new__(Formula)
        # c++, value rather than reference
        ret.elements=self.elements
        ret.isotopes=self.isotopes
        return ret

    cdef void add_(self, Formula f)except *:
        cdef int_pair i
        cdef ints_pair it
        for i in f.elements:
            self.setE(i.first,self.getE(i.first)+i.second)
        for it in f.isotopes:
            self.setI(it.first.first,it.first.second,self.getI(it.first.first,it.first.second)+(it.second))

    cdef void sub_(self, Formula f)except *:
        cdef int_pair i
        cdef ints_pair it
        # isotopes first
        for it in f.isotopes:
            self.setI(it.first.first,it.first.second,self.getI(it.first.first,it.first.second)-it.second)
        for i in f.elements:
            self.setE(i.first,self.getE(i.first)-i.second)

    cdef void mul_(self, int32_t times)except *:
        if times<=0:
            if times==0:
                self.clear()
                return
            raise ValueError("times should be in 0,1,...")

        i = self.elements.begin()
        it = self.isotopes.begin()
        while i!=self.elements.end():
            # cython bug
            # deref(i).second*=times
            deref(i).second = deref(i).second*times
            inc(i)
        while it!=self.isotopes.end():
            deref(it).second=deref(it).second*times
            inc(it)

    cdef bool eq(self, Formula f):
        if not _elements_eq(self.elements, f.elements):
            return False
        if self.isotopes.size()!=f.isotopes.size():
            return False
        i1 = self.isotopes.begin()
        i2 = f.isotopes.begin()
        while i1!=self.isotopes.end():
            if deref(i1)!=deref(i2):
                return False
            inc(i1)
            inc(i2)
        return True

    cdef bool contains(self, Formula f):
        if self.elements.size()< f.elements.size() or self.isotopes.size()<f.isotopes.size():
            return False

        cdef int_pair i
        for i in f.elements:
            if self.getE(i.first)-self.getI(i.first,0)<i.second-f.getI(i.first,0):
                return False
        cdef ints_pair ii
        for ii in f.isotopes:
            if self.getI(ii.first.first,ii.first.second)<ii.second:
                return False
        return True

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def to_numpy(self):
        '''
        atomic number | mass number | number
        '''
        cdef np.ndarray[np.int32_t, ndim=2] ret = np.empty((self.elements.size()+self.isotopes.size(),3),dtype=np.int32)
        cdef int32_t i = 0
        cdef int_pair it
        for it in self.elements:
            ret[i,0]=it.first
            ret[i,1]=0
            ret[i,2]=it.second
            inc(i)
        cdef ints_pair iit
        for iit in self.isotopes:
            ret[i,0]=iit.first.first
            ret[i,1]=iit.first.second
            ret[i,2]=iit.second
            inc(i)
        return ret

    def to_dict(self):
        cdef dict ret = {}
        cdef int_pair it
        cdef ints_pair iit
        for it in self.elements:
            ret[elements[it.first]] = it.second - self.getI(it.first, 0)
        for iit in self.isotopes:
            ret[f"{elements[iit.first.first]}[{iit.first.second}]"] = iit.second
        return ret

    @staticmethod
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def from_numpy(np.ndarray[np.int_t, ndim=2] data):
        assert data.shape[1]==3
        cdef Formula f = Formula.__new__(Formula)
        cdef int32_t i
        for i in range(data.shape[0]):
            if data[i,1]==0:
                f.setE(data[i,0],data[i,2])
            else:
                f.setI(data[i,0],data[i,1],data[i,2])
        return f

    def __setitem__(self, str key, int32_t num):
        cdef int_pair e = str2element(key)
        if e.second==0:
            self.setE(e.first, num)
        elif elementMassNum[e.first]==e.second:
            self.setE(e.first, num + self.getI(e.first, 0)) # 0到底包不包含自己啊……
        elif elementMassDist[e.first].find(e.second) != elementMassDist[e.first].end():
            self.setI(e.first, e.second, num)
        else:
            raise KeyError(f'have no element {key}')
        
    def __getitem__(self, str key):
        cdef int_pair p = str2element(key)
        if p.second == 0:
            return self.getE(p.first)
        elif elementMassNum[p.first]==p.second:
            return self.getE(p.first)-self.getI(p.first,0)
        else:
            return self.getI(p.first, p.second)


    def __str__(self):
        return self.toStr(False, True)
    
    def __repr__(self):
        return self.toStr(False, True)

    def __copy__(self):
        return self.copy()

    def __iadd__(self, Formula f):
        self.add_(f)
        return self

    def __add__(self, Formula f):
        cdef Formula ret = Formula.copy(self)
        ret.add_(f)
        return ret

    def __isub__(self, Formula f):
        self.sub_(f)
        return self

    def __sub__(self, Formula f):
        cdef Formula ret = Formula.copy(self)
        ret.sub_(f)
        return ret

    def __imul__(self, int32_t t):
        self.mul_(t)
        return self

    def __mul__(first, second):
        cdef Formula ret
        if isinstance(first, Formula):
            ret = Formula.copy(first)
            ret.mul_(second)
        else:
            ret = Formula.copy(second)
            ret.mul_(first)
        return ret

    def __eq__(self, Formula f):
        return self.eq(f)

    def __contains__(self, Formula f):
        return self.contains(f)

    def __hash__(self):
        cdef int ret = 0
        cdef int_pair i
        cdef ints_pair it
        for i in self.elements:
            ret^=hash((i.first<<hash_factor)+i.second)
        for it in self.isotopes:
            ret^=hash((((it.first.first<<hash_factor)+it.first.second)<<hash_factor)+it.second)
        return ret