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
import re
from typing import Union

import cython
import numpy as np
cimport numpy as np

from ._element cimport _factor, _andfactor, elements, elementsMap, elementMass,\
     elementMassNum , elementMassDist, elementNumMap, elementParasMap, CHmin, \
     encodeIsotope, decodeIsotope, str2element, element2str, str2code, code2str


_elementsOrder = ['C', 'H', 'O', 'N', 'S']

cdef vector[int] elementsOrder = [elementsMap[e] for e in _elementsOrder]
cdef unordered_set[int] elementsOrderSet = set(elementsOrder)

cdef int encodeMNum(int m, int num):
    return (m<<_factor)+num

cdef void decodeMNum(int code, int*m, int*num):
    m[0] = code>>_factor
    num[0] = code&_andfactor

cdef double _elements_mass(unordered_map[int, int] & elements):
    cdef double mass = 0
    cdef pair[int, int] i
    for i in elements:
        mass+=elementMass[i.first]*i.second
    return mass

cdef double _elements_DBE(unordered_map[int, int] & elements):
    cdef double dbe2 = 2
    cdef pair[int, int] i
    for i in elements:
        dbe2 += i.second * elementParasMap[i.first][0]
    return dbe2 / 2

cdef double _elements_Omin(unordered_map[int, int] & elements):
    cdef double ret = 0
    cdef pair[int, int] i
    for i in elements:
        ret+=i.second*elementParasMap[i.first][3]
    return ret

cdef double _elements_Omax(unordered_map[int, int]&elements):
    cdef double ret = 0
    cdef pair[int, int] i
    for i in elements:
        ret+=i.second*elementParasMap[ i.first ][4]
    return ret

cdef double _elements_Hmin(unordered_map[int, int]&elements):
    cdef double ret = -0.5
    cdef pair[int, int] i
    for i in elements:
        if i.first==6: # C
            ret+=CHmin[i.second]
        else:
            ret+=i.second*elementParasMap[i.first][1]
    return ret

cdef double _elements_Hmax(unordered_map[int, int]&elements):
    cdef double ret = 2.5
    cdef pair[int, int] i
    for i in elements:
        ret+=i.second*elementParasMap[ i.first ][2]
    return ret

cdef bool _elements_eq(unordered_map[int, int]&_f1,unordered_map[int, int]&_f2):
    if _f1.size()!=_f2.size():
        return False
    cdef pair[int, int] i
    cdef unordered_map[int, int].iterator it
    for i in _f1:
        it = _f2.find(i.first)
        if it==_f2.end() or i.second != deref(it).second:
            return False
    return True

cdef double _mass_isotopes_mass(double mass, cpplist[pair[int, int]]&isotopes):
    cdef pair[int, int] i
    cdef int m, num
    for i in isotopes:
        decodeMNum(i.second, &m, &num)
        mass+=num*(elementMassDist[i.first][m].first-elementMass[i.first])
    return mass

cdef double _elements_isotopes_mass(unordered_map[int, int]&elements, cpplist[pair[int, int]]&isotopes):
    return _mass_isotopes_mass(_elements_mass(elements), isotopes)
    

cdef class Formula:
    def __init__(self, formula : Union[str, dict] = None, **kwargs):
        '''
        Formula('CC[13]H5O-')
        Formula({'C':1,'C[13]':1,'H':5,'O':1},charge=-1)
        Formula({'C':1,'C[13]':1,'H':5,'O':1,'charge'=-1})
        Formula(C=1,H=2,O=1,charge=-1)
        '''
        try:
            if isinstance(formula, str):
                if not re.fullmatch(r"([A-Z][a-z]{0,2}(\[\d+\])?\d*)*[-+]?", formula):
                    raise ValueError(str(formula))
                charge = formula[-1]
                if charge == '+':
                    self.setE(0,-1)
                elif charge == '-':
                    self.setE(0,1)
                for match in re.finditer(r"([A-Z][a-z]{0,2})(\[\d+\])?(\d*)", formula):
                    e = match.group(1)
                    m = match.group(2)
                    if m is None:
                        m = 0
                    else:
                        m = int(m[1:-1])
                    num = match.group(3)
                    if len(num) == 0:
                        self.addElement(e, m)
                    else:
                        self.addElement(e, m, int(num))
            else:
                dic = kwargs.copy()
                if isinstance(formula, dict):
                    for k, v in formula.items():
                        dic[k] = v
                for k, v in dic.items():
                    match = re.fullmatch(r"([A-Z][a-z]{0,2})(\[\d+\])?", k)
                    if match is not None:
                        e = match.group(1)
                        m = match.group(2)
                        if m is None:
                            m = 0
                        else:
                            m = int(m[1:-1])
                        self.addElement(e, m, v)
                    elif k == 'charge':
                        self.setE(0,-v)
                    else:
                        raise ValueError('wrong kwargs'+k)
        except ValueError as e:
            raise ValueError('wrong formula:' + str(e))
        
    property charge:
        def __get__(self):
            return -self.getE(0)

        def __set__(self, int value):
            self.setE(0, -value)
            
    @property
    def isIsotope(self):
        return self.isotopes.size() > 0

    cpdef double mass(self):
        return _elements_isotopes_mass(self.elements, self.isotopes)

    cpdef Formula findOrigin(self):
        cdef Formula formula = Formula.__new__(Formula)
        formula.elements=self.elements
        return formula

    cpdef double DBE(self):
        return _elements_DBE(self.elements)

    cdef double Omin(self):
        return _elements_Omin(self.elements)
    
    cdef double Omax(self):
        return _elements_Omax(self.elements)
    
    cdef double Hmin(self):
        return _elements_Hmin(self.elements)

    cdef double Hmax(self):
        return _elements_Hmax(self.elements)

    cpdef void addElement(self, str element, int m = 0, int num=1) except *:
        cdef int index = elementsMap.get(element, -1)
        if index == -1:
            raise ValueError(f'unknown element:{element}')
        self.addEI(index, m, num)


    cdef void addEI(self, int index, int m, int num) except *:
        # if num == 0:
        #     return
        self.setE(index, self.getE(index) + num)
        if m > 0:
            if elementMassDist[index].find(m) == elementMassDist[index].end():
                raise ValueError(f'unknown element:{elements[index]}[{m}]')
            if elementMassNum[index] != m:  # isotope
                self.setI(index, m, self.getI(index, m) + num)

    @staticmethod
    cdef str eToStr(int index, int num, bool showProton):
        cdef str e= f"{elements[index]}[{elementMassNum[index]}]" if showProton else elements[index]
        if num==1:
            return e
        elif num>1:
            return e+str(num)
        else:
            return ''
    @staticmethod
    cdef str iToStr(int index, int m, int num):
        if num==1:
            return f"{elements[index]}[{m}]"
        elif num>1:
            return f"{elements[index]}[{m}]{num}"
        else:
            return ''

    cpdef toStr(self, bool showProton = False, bool withCharge = True):
        cdef list rets=[]
        cdef unordered_map[int, int] isotopes
        cdef pair[int, int] li
        for li in self.isotopes:
            isotopes[li.first]+=1

        cdef unordered_map[int, int].iterator it, isoit
        cdef int i, index, num
        for i in elementsOrder:
            it = self.elements.find(i)
            if it != self.elements.end():
                index = deref(it).first
                num = deref(it).second
                isoit = isotopes.find(index)
                if isoit==isotopes.end():
                    rets.append(Formula.eToStr(index, num, showProton))
                else:
                    rets.append(Formula.eToStr(index, num-self.getI(index,0), showProton))
                    isotopes.erase(isoit)
                    for li in self.isotopes:
                        if li.first == index:
                            rets.append(Formula.iToStr(index,li.second>>_factor,li.second&_andfactor))

        cdef pair[int, int] ei
        cdef unordered_set[int].iterator sit
        for ei in self.elements:
            index=ei.first
            if index > 0:
                num=ei.second
                sit = elementsOrderSet.find(index)
                if sit == elementsOrderSet.end():
                    isoit = isotopes.find(index)
                    if isoit==isotopes.end():
                        rets.append(Formula.eToStr(index, num, showProton))
                    else:
                        rets.append(Formula.eToStr(index, num-self.getI(index,0), showProton))
                        isotopes.erase(isoit)
                        for li in self.isotopes:
                            if li.first == index:
                                rets.append(Formula.iToStr(index,li.second>>_factor,li.second&_andfactor))
                  
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

    cpdef double relativeAbundance(self):
        if not self.isIsotope:
            return 1
        return pyteomics.mass.isotopic_composition_abundance(formula=self.toStr(True, False)) /\
            pyteomics.mass.isotopic_composition_abundance(
                formula=self.findOrigin().toStr(True, False))

    cpdef void clear(self):
        self.elements.clear()
        self.isotopes.clear()

    cdef void setE(self, int index, int num) except *:
        if index != 0 and num<self.getI(index,0):
            raise ValueError(f"the number of {index} '{elements[index]}' shouldn't be lesser than {self.getI(index,0)}")
        
        cdef unordered_map[int, int].iterator it
        if num==0:
            it = self.elements.find(index)
            if it != self.elements.end():
                self.elements.erase(it)
            return
        self.elements[index] = num

    cdef int getE(self, int index):
        '''
        contains isotopes
        '''
        cdef unordered_map[int, int].iterator it = self.elements.find(index)
        if it == self.elements.end():
            return 0
        return deref(it).second

    cdef void setI(self, int index, int m, int num) except *:
        '''
        wouldn't change elements' nums
        eg. C2 -> setI(6,13,1) -> CC[13]
            spectial: setI(6,0,0) # clear
        '''
        if num<0:
            raise ValueError(f"the number of {index} '{elements[index]}[{m}]' shouldn't be lesser than 0")
        cdef cpplist[pair[int, int]].iterator it = self.isotopes.begin()
        if num==0:
            if m==0:
                while it!=self.isotopes.end():
                    if deref(it).first == index:
                        it=self.isotopes.erase(it)
                    else:
                        inc(it)
            else:
                while it!=self.isotopes.end():
                    if deref(it).first == index and (deref(it).second >> _factor) == m:
                        self.isotopes.erase(it)
                        return
                    else:
                        inc(it)
        else:
            if m==0:
                raise ValueError("if m==0, index must equal to 0")
            if self.getE(index)<self.getI(index,0)-self.getI(index,m)+num:
                raise ValueError(f"the number of {index} '{elements[index]}[{m}]' shouldn't be greater than {self.getE(index)-self.getI(index,0)+self.getI(index,m)}")
            while it!=self.isotopes.end():
                if deref(it).first == index and (deref(it).second >> _factor) == m:
                    deref(it).second = encodeMNum(m, num)
                    return
                inc(it)
            self.isotopes.push_back(pair[int,int](index, encodeMNum(m, num)))

    cdef int getI(self, int index, int m):
        '''
        CC[13]C[14] -> getI(6,m = 0) -> 2
        '''
        cdef pair[int, int] i
        cdef int ret = 0
        if m != 0:
            for i in self.isotopes:
                if i.first == index and (i.second >> _factor) == m:
                    ret = i.second & _andfactor
                    break
        else:
            for i in self.isotopes:
                if i.first == index:
                    ret += i.second & _andfactor
        return ret

    cdef Formula copy(self):
        cdef Formula ret = Formula.__new__(Formula)
        # c++, value rather than reference
        ret.elements=self.elements
        ret.isotopes=self.isotopes
        return ret

    cdef void add_(self, Formula f)except *:
        cdef pair[int, int] i
        for i in f.elements:
            self.setE(i.first,self.getE(i.first)+i.second)
        for i in f.isotopes:
            self.setI(i.first,i.second>>_factor,self.getI(i.first,i.second>>_factor)+(i.second&_andfactor))

    cdef void sub_(self, Formula f)except *:
        cdef pair[int, int] i
        # isotopes first
        for i in f.isotopes:
            self.setI(i.first,i.second>>_factor,self.getI(i.first,i.second>>_factor)-(i.second&_andfactor))
        for i in f.elements:
            self.setE(i.first,self.getE(i.first)-i.second)

    cdef void mul_(self, int times)except *:
        if times<=0:
            if times==0:
                self.clear()
                return
            raise ValueError("times should be in 0,1,...")

        cdef unordered_map[int,int].iterator i = self.elements.begin()
        cdef cpplist[pair[int,int]].iterator it = self.isotopes.begin()
        while i!=self.elements.end():
            # cython bug
            # deref(it).second*=times
            self.elements[deref(i).first]=times*deref(i).second
            inc(i)
        while it!=self.isotopes.end():
            deref(it).second=(deref(it).second>>_factor<<_factor)+(deref(it).second&_andfactor)*times
            inc(it)

    cdef bool eq(self, Formula f):
        if not _elements_eq(self.elements, f.elements):
            return False
        if self.isotopes.size()!=f.isotopes.size():
            return False
        cdef pair[int, int] i, j
        cdef bool flag 
        for i in self.isotopes:
            flag = False
            for j in f.isotopes:
                if i.first==j.first and i.second==j.second:
                    flag=True
            if not flag:
                return False
        return True

    cdef bool contains(self, Formula f):
        if self.elements.size()< f.elements.size() or self.isotopes.size()<f.isotopes.size():
            return False

        cdef pair[int, int] i
        for i in f.elements:
            if self.getE(i.first)-self.getI(i.first,0)<i.second-f.getI(i.first,0):
                return False
        for i in f.isotopes:
            if self.getI(i.first,i.second>>_factor)<i.second&_andfactor:
                return False
        return True

    @cython.boundscheck(False)
    def to_numpy(self):
        '''
        atomic number | mass number | number
        '''
        cdef np.ndarray[np.int_t, ndim=2] ret = np.empty((self.elements.size()+self.isotopes.size(),3),dtype=int)
        cdef int i = 0
        cdef pair[int, int] it
        for it in self.elements:
            ret[i,0]=it.first
            ret[i,1]=0
            ret[i,2]=it.second
            inc(i)
        for it in self.isotopes:
            ret[i,0]=it.first
            ret[i,1]=it.second>>_factor
            ret[i,2]=it.second&_andfactor
            inc(i)
        return ret

    @staticmethod
    @cython.boundscheck(False)
    def from_numpy(np.ndarray[np.int_t, ndim=2] data):
        assert data.shape[1]==3
        cdef Formula f = Formula.__new__(Formula)
        cdef int i
        for i in range(data.shape[0]):
            if data[i,1]==0:
                f.setE(data[i,0],data[i,2])
            else:
                f.setI(data[i,0],data[i,1],data[i,2])
        return f

    def __setitem__(self, str key, int num):
        cdef int index, m
        str2element(key, &index, &m)
        if m==0:
            self.setE(index, num)
        elif elementMassNum[index]==m:
            self.setE(index, num + self.getI(index, 0))
        elif elementMassDist[index].find(m) != elementMassDist[index].end():
            self.setI(index, m, num)
        else:
            raise KeyError(f'have no element {key}')
        
    def __getitem__(self, str key):
        cdef int index ,m
        str2element(key, &index, &m)
        if m == 0:
            return self.getE(index)
        elif elementMassNum[index]==m:
            return self.getE(index)-self.getI(index,0)
        else:
            return self.getI(index, m)


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

    def __imul__(self, int t):
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
        cdef pair[int, int] i
        for i in self.elements:
            ret^=hash((i.first<<_factor)+i.second)
        for i in self.isotopes:
            ret^=hash((i.first<<(_factor<<1))+i.second)
        return ret