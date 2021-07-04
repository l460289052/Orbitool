# distutils: language = c++
# cython: language_level = 3

from cython.operator cimport (
    dereference as deref, preincrement as preinc, predecrement as predec,
    postdecrement as postdec, postincrement as postinc)
from libc.stdint cimport int32_t
from libc.math cimport fabs, remainder, ceil, floor
from libcpp.stack cimport stack

from ._element cimport(
    elements as e_elements, elementMass, elementMassDist, elementMassNum,
    str2element, element2str, int_pair, dou_pair) 
from ._formula cimport (
    Formula, int_map, ints_pair, ints_map, _elements_mass,
    _mass_isotopes_mass)

cdef double eps = 1e-9

cdef int HIndex = 1, CIndex = 6, OIndex = 8

cdef _elements_sum(vector[double]& v, int_map& elements, double init):
    cdef int_pair p
    for p in elements:
        init += p.second * v[p.first]
    return init

cdef void _state_inc(State& state, State& other):
    state.DBE2+=other.DBE2
    state.HMin+=other.HMin
    state.HMax+=other.HMax
    state.OMin+=other.OMin
    state.OMax+=other.OMax

cdef void _state_dec(State& state, State& other):
    state.DBE2-=other.DBE2
    state.HMin-=other.HMin
    state.HMax-=other.HMax
    state.OMin-=other.OMin
    state.OMax-=other.OMax

cdef void _state_add(State& state, State& other, int num):
    state.DBE2+=other.DBE2*num
    state.HMin+=other.HMin*num
    state.HMax+=other.HMax*num
    state.OMin+=other.OMin*num
    state.OMax+=other.OMax*num

cdef class Calculator:
    def __init__(self):
        self.rtol = 1e-6
        cdef int32_t length = elementMass.size()
        self.ElementNumMin.resize(length,0)
        self.ElementNumMax.resize(length,0)
        self.ElementDbe2.resize(length,0)
        self.ElementHMin.resize(length,0)
        self.ElementHMax.resize(length,0)
        self.ElementOMin.resize(length,0)
        self.ElementOMax.resize(length,0)
        self.ElementState.resize(length)
        self.ElementInited.resize(length, False)

        self.calcedElements.push_back(CIndex)
        self.calcedElements.push_back(HIndex)
        self.calcedElements.push_back(OIndex)
        self.DBEMin = 0
        self.DBEMax = 8
        self.MMin = 50
        self.MMax = 750
        self.nitrogenRule = False

        init_params = [ 
            ('e', -1, 1, -1, -0.5, -0.5, 0, 0),
            ('C', 0, 20, 2, 0, 2, 0, 3),
            ('H', 0, 40, -1, -1, -1, 0, 0),
            ('O', 0, 15, 0, 0, 0, -1, -1),
            ('N', 0, 4, 1, -1, 1, 0, 3),
            ('S', 0, 3, 0, 0, 0, 0, 4),
            ('Li', 0, 3, -1, 0, 0, 0, 0),
            ('Na', 0, 3, -1, 0, 0, 0, 0),
            ('K', 0, 3, -1, 0, 0, 0, 0),
            ('F', 0, 15, -1, -1, 0, 0, 0),
            ('Cl', 0, 3, -1, -1, 0, 0, 3),
            ('Br', 0, 3, -1, -1, 0, 0, 3),
            ('I', 0, 3, -1, -1, 0, 0, 3),
            ('P', 0, 4, 1, -1, 1, 0, 6),
            ('Si', 0, 5, 2, 0, 2, 0, 3)]
        for row in init_params:
            self[row[0]] = {"Min":row[1], "Max":row[2], "DBE2":row[3], "HMin":row[4], "HMax":row[5], "OMin":row[6], "OMax":row[7]}
        
    cdef double OMin(self, int_map& elements):
        return _elements_sum(self.ElementOMin, elements, 0)
    
    cdef double OMax(self, int_map& elements):
        return _elements_sum(self.ElementOMax, elements, 0)

    cdef double HMin(self, int_map& elements):
        return _elements_sum(self.ElementHMin, elements, -0.5)
    
    cdef double HMax(self, int_map& elements):
        return _elements_sum(self.ElementHMax, elements, 2.5)
    
    cdef double DBE(self, int_map& elements):
        return _elements_sum(self.ElementDbe2, elements, 2.0) / 2.0
        
    def setEI(self, str key, bool use = True):
        cdef int_pair p = str2element(key)
        if p.second == 0 or p.second == elementMassNum[p.first]:
            if not use and (p.first == OIndex or p.first==HIndex or p.first==CIndex):
                raise KeyError('cannot disable C, H, O')
            it = self.calcedElements.begin()
            while it != self.calcedElements.end():
                if deref(it) == p.first:
                    if not use:
                        self.calcedElements.erase(it)
                    return
                preinc(it)
            if use:
                self.calcedElements.push_back(p.first)
        else:
            iit = self.calcedIsotopes.begin()
            while iit!=self.calcedIsotopes.end():
                if deref(iit) == p:
                    if not use:
                        self.calcedIsotopes.erase(iit)
                    return
                preinc(iit)
            if use:
                self.calcedIsotopes.push_back(p)
                
    def getInitedElements(self):
        cdef int32_t i
        cdef bool v
        return [e_elements[i] for i, v in enumerate(self.ElementInited) if v]
                
    def getElements(self):
        cdef int32_t i
        return [e_elements[i] for i in self.calcedElements]

    def getIsotopes(self):
        cdef int_pair p
        return [element2str(p) for p in self.calcedIsotopes]
    
    cdef bool isCovered(self, double l, double r):
        it = self.mCover.upper_bound(l+eps)
        return not (it==self.mCover.begin()) and r<=deref(predec(it)).second + eps

    cdef void cover(self, double l, double r):
        cdef double ll=l, rr=l
        l+=eps

        it = self.mCover.upper_bound(l)
        if it!=self.mCover.begin():
            if deref(predec(it)).second>ll:
                if deref(it).second>r:
                    return
                ll = deref(it).first
                self.mCover.erase(postinc(it))
            else:
                preinc(it)
        while it!=self.mCover.end() and deref(it).first < r:
            rr = deref(it).second
            self.mCover.erase(postinc(it))
            
        if rr<r:
            rr=r
        self.mCover.insert(it, dou_pair(ll,rr))
        
    cdef int32_t checkParameters(self):
        cdef int32_t e
        for e in self.calcedElements:
            if not self.ElementInited[e]:
                return -e
        return 1
    
    def __setitem__(self, str e, dict v):
        cdef int_pair p = str2element(e)
        assert p.second == 0
        cdef State state = State(DBE2 = v["DBE2"], OMin = v["OMin"], OMax = v["OMax"], HMin = v["HMin"], HMax = v["HMax"])
        self.ElementState[p.first] = state
        self.ElementNumMin[p.first] = v["Min"]
        self.ElementNumMax[p.first] = v["Max"]
        
        self.ElementDbe2[p.first] = v["DBE2"]
        self.ElementHMin[p.first] = v["HMin"]
        self.ElementHMax[p.first] = v["HMax"]
        self.ElementOMin[p.first] = v["OMin"]
        self.ElementOMax[p.first] = v["OMax"]
        self.ElementInited[p.first] = True

    def __getitem__(self, str e):
        cdef int32_t p = str2element(e).first
        cdef State state = self.ElementState[p]
        cdef dict d = {"Min":self.ElementNumMin[p],"Max":self.ElementNumMax[p],
            "DBE2":state.DBE2, "HMin":state.HMin, "HMax":state.HMax, "OMin":state.OMin,
            "OMax":state.OMax}
        return d
    
    def __delitem__(self, str e):
        cdef int32_t p = str2element(e).first
        self.ElementInited[p] = False
    
    cdef setStateForFormula(self, State&state, int_map&elements):
        state.DBE2 = _elements_sum(self.ElementDbe2, elements, 2.0)
        state.OMin = self.OMin(elements)
        state.OMax = self.OMax(elements)
        state.HMin = self.HMin(elements)
        state.HMax = self.HMax(elements)

    
    cpdef void calc(self, double MMin = -1, double MMax = -1) except*:
        if self.checkParameters() < 0:
            raise ValueError(f"Please check element {e_elements[int(-self.checkParameters())]}")
        cdef double ML = self.MMin
        cdef double MR = self.MMax
        if MMin>0 and MMax>0:
            ML = MMin
            MR = MMax
        else:
            self.clear()
        if self.isCovered(ML, MR):
            return
        cdef double DBE2Min = self.DBEMin*2
        cdef double DBE2Max = self.DBEMax*2

        cdef Formula f = Formula.__new__(Formula)
        f.charge = self.charge

        cdef int32_t CNum, ONum, HNum, num, index, CMin, CMax, OMax, HMax, numMax, step
        cdef cpplist[int32_t] elements
        cdef cpplist[int32_t].iterator eit
        cdef stack[int32_t] elementNum, elementMax
        cdef stack[double] emass
        cdef double mass
        cdef bool nitrogenRule = self.nitrogenRule
        if nitrogenRule:
            step = 2
        else:
            step = 1

        elements.push_back(CIndex)
        for num in self.calcedElements:
            if num !=HIndex and num!=CIndex and num!=OIndex:
                elements.push_back(num)

        cdef State state
        CMin = self.ElementNumMin[CIndex]
        CMax = min(<int>(MR/elementMass[CIndex]), self.ElementNumMax[CIndex])
        for CNum in range(CMin, CMax+1):
            f.setE(CIndex, CNum)
            self.setStateForFormula(state, f.elements)
            elementNum.push(CNum)
            elementMax.push(CNum)
            emass.push(f.mass())
            eit = elements.begin()
            while True:
                # print(str(f), elementNum)
                if elementNum.top() > elementMax.top():
                    index = deref(eit)
                    _state_add(state, self.ElementState[index], -elementNum.top())
                    elementNum.pop()
                    elementMax.pop()
                    emass.pop()

                    f.setE(deref(postdec(eit)),0) # *eit--
                elif preinc(eit)!=elements.end():
                    index = deref(eit)
                    num = self.ElementNumMin[index]
                    elementNum.push(num)
                    numMax = min(self.ElementNumMax[index],<int>((MR - emass.top())/elementMass[index]))
                    elementMax.push(numMax)
                    if num>0:
                        _state_add(state, self.ElementState[index], num)
                        emass.push(emass.top()+elementMass[index]*num)
                    else:
                        emass.push(emass.top())
                    f.setE(index, num)
                    continue
                else:
                    mass=emass.top()
                    ONum=max(self.ElementNumMin[OIndex], <int>max(state.OMin, ceil((ML-mass-elementMass[HIndex]*state.HMax)/elementMass[OIndex])))
                    OMax=min(self.ElementNumMax[OIndex], <int>min(state.OMax, (MR-mass-elementMass[HIndex]*state.HMin)/elementMass[OIndex]))
                    if ONum<=OMax:
                        # print(f, state.DBE2, state.HMin, state.HMax, state.OMin, state.OMax, mass, f.mass())

                        mass+=elementMass[OIndex]*ONum
                        while ONum<=OMax:
                            f.setE(OIndex,ONum)
                            # O can't affect DBE and HNum, so don't change state 
                            HNum=max(self.ElementNumMin[HIndex], <int>ceil(max(state.HMin, (ML-mass)/elementMass[HIndex], (DBE2Max-state.DBE2)/self.ElementDbe2[HIndex])))
                            HMax=min(self.ElementNumMax[HIndex], <int>min(state.HMax, (MR-mass)/elementMass[HIndex], (DBE2Min-state.DBE2)/self.ElementDbe2[HIndex]))
                            if nitrogenRule and fabs(remainder(state.DBE2+HNum*self.ElementDbe2[HIndex], 2.0))>eps:
                                preinc(HNum)
                            
                            while HNum<=HMax:
                                f.setE(HIndex,HNum)
                                mass = _elements_mass(f.elements)
                                
                                # print(f"insert {f}")

                                self.insertElements(f.elements, mass)
                                self.insertIsotopes(f.elements, mass)
                                HNum+=step
                            preinc(ONum)
                            mass+=elementMass[OIndex]
                    f.setE(OIndex,0)
                    f.setE(HIndex,0)
                    
                    predec(eit)
                # inc
                index=deref(eit)
                num = elementNum.top()+1
                elementNum.pop()
                emass.pop()
                if elementNum.empty():
                    elementMax.pop()
                    break
                elementNum.push(num)
                emass.push(emass.top()+elementMass[index]*num)
                f.setE(index, num)
                _state_inc(state, self.ElementState[index])
        self.cover(ML,MR)

        # print(self.isotopes.size())
        # cdef pair[double, pair[double, cpplist[pair[int, int]]]] isotope
        # for isotope in self.isotopes:
        #     print(isotope)
        
    cpdef clear(self):
        self.formulas.clear()
        self.isotopes.clear()
        self.mCover.clear()
        
    def get(self, double M):
        cdef double ML,MR,delta
        delta = self.rtol*M
        ML=M-delta
        MR=M+delta
        if not self.isCovered(ML,MR):
            self.calc(ML,MR)
        
        cdef list ret = list()
        if self.formulas.empty():
            return ret
        it1 = self.formulas.lower_bound(ML)
        it2 = self.formulas.lower_bound(MR)
        cdef Formula formula
        while it1!=it2:
            formula = Formula.__new__(Formula)
            formula.elements = deref(it1).second
            ret.append(formula)
            preinc(it1)

        iit1 = self.isotopes.lower_bound(ML)
        iit2 = self.isotopes.lower_bound(MR)
        while iit1!=iit2:
            formula = Formula.__new__(Formula)
            it1 = self.getFormula(deref(iit1).second.first).second
            formula.elements = deref(it1).second
            formula.isotopes = deref(iit1).second.second
            ret.append(formula)
            preinc(iit1)
        return ret

    cdef pair[bool, map[double, map[int32_t, int32_t]].iterator] getFormula(self, double& mass):
        cdef pair[bool, map[double, map[int32_t, int32_t]].iterator] it
        if self.formulas.empty():
            it.first = False
            it.second = self.formulas.end()
            return it
        it.second = self.formulas.upper_bound(mass)
        if it.second != self.formulas.end():
            if fabs(deref(it.second).first - mass) < eps:
                it.first = True
                return it
            elif it.second == self.formulas.begin():
                it.first = False
                return it
        if fabs(deref(predec(it.second)).first - mass) > eps:
            preinc(it.second)
            it.first = False
        return it

    
    cdef void insertElements(self, int_map&elements, double mass = -1):
        if mass<0:
            mass = _elements_mass(elements)
        it = self.getFormula(mass)
        if not it.first:
            self.formulas.insert(it.second, d_ii_map_pair(mass, elements))
    

    cdef void insertIsotopes(self, int_map&elements, double mass = -1):
        if mass<0:
            mass = _elements_mass(elements)
        
        cdef int_pair i
        # cdef map[int32_t, int32_t].iterator it
        cdef ints_map isotopes

        for i in self.calcedIsotopes:
            it = elements.find(i.first)
            if it == elements.end():
                continue
            isotopes.clear()

            # double
            if deref(it).second > 1:
                isotopes[i] = 2
                self.insertIsotope(mass, isotopes)
            # single
            isotopes[i] = 1
            self.insertIsotope(mass, isotopes)
            
            # multi(2)
            for j in self.calcedIsotopes:
                if i==j:
                    break
                if elements.find(j.first)==elements.end():
                    continue
                isotopes[j] = 1
                self.insertIsotope(mass, isotopes)
                isotopes.erase(j)

    cdef void insertIsotope(self, double&mass, ints_map& isotopes):
        cdef pair[bool, map[double, pair[double, map[pair[int32_t, int32_t], int32_t]]].iterator] it
        isomass = _mass_isotopes_mass(mass, isotopes)
        it = self.getIsotope(isomass)
        if not it.first:
            self.isotopes.insert(it.second, d_d_ii_i_map_pair_pair(isomass, d_ii_i_map_pair(mass, isotopes)))

    cdef pair[bool, map[double, pair[double, map[pair[int32_t, int32_t], int32_t]]].iterator] getIsotope(self, double&mass):
        cdef pair[bool, map[double, pair[double, map[pair[int32_t, int32_t], int32_t]]].iterator] it
        if self.isotopes.empty():
            it.second = self.isotopes.end()
            it.first = False
            return it
        it.second = self.isotopes.upper_bound(mass)
        if it.second!=self.isotopes.end():
            if fabs(deref(it.second).first-mass)<eps:
                it.first = True
                return it
            elif it.second == self.isotopes.begin():
                it.first = False
                return it
            
        if fabs(deref(predec(it.second)).first - mass) < eps:
            it.first = True
            return it
        else:
            preinc(it.second)
            it.first = False
            return it