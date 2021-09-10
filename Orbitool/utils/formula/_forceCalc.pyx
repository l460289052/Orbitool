from cython.operator cimport (
    dereference as deref, preincrement as preinc, predecrement as predec,
    postdecrement as postdec, postincrement as postinc)
from libc.math cimport ceil
from libcpp cimport bool
from libcpp.deque cimport deque
from libcpp.vector cimport vector
from libcpp.unordered_map cimport unordered_map

from itertools import product

from ._element cimport( 
    getMass, str2element, element2str,
    elementMassNum, elementMass)
from ._formula cimport Formula

cdef int CIndex = 6, HIndex = 1, OIndex = 8

cdef void incState(State& state):
    preinc(state.num)
    state.massSum = state.massSum + state.mass
    
cdef Formula isotopes2formula(deque[State]&isotopes):
    cdef State i
    cdef Formula f = Formula.__new__(Formula)
    for i in isotopes:
        f.addEI(i.isotope.first, i.isotope.second, i.num)
    # print(f)
    return f

cdef class Calculator:
    def __init__(self):
        self.rtol = 1e-6

        cdef int i
        cdef vector[int] l = [CIndex, HIndex, OIndex]
        cdef int_pair p
        p.second = 0
        for i in l:
            p.first = i
            self.calcedIsotopes[getMass(p)] = p
            self.isotopeMaximum[p] = 999
            
    cdef void calcStateNum(self, State&state, double MR):
        cdef double mass = state.massSum
        state.numMax = min(<int>((MR-mass)/state.mass), self.isotopeMaximum[state.isotope])

    def __setitem__(self, str e, int32_t value):
        cdef int_pair p = str2element(e)
        if p.second == elementMassNum[p.first]:
            p.second = 0
        it = self.calcedIsotopes.begin()
        while it!=self.calcedIsotopes.end():
            if deref(it).second == p:
                break
            preinc(it)
        
        if it == self.calcedIsotopes.end():
            if value > 0:
                self.calcedIsotopes[getMass(p)] = p
                self.isotopeMaximum[p] = value
        else:
            if value <= 0:
                self.calcedIsotopes.erase(it)
                self.isotopeMaximum.erase(p)
            else:
                self.isotopeMaximum[p] = value


    def __getitem__(self, str e):
        cdef int_pair p = str2element(e)
        it = self.isotopeMaximum.find(p)
        if it == self.isotopeMaximum.end():
            return 0
        else:
            return deref(it).second
            
    def getEIList(self):
        cdef ints_pair p
        return [element2str(p.first) for p in self.isotopeMaximum]
    
    def get_direct(self, double M, Formula base_group):
        """
        if base_group contains an unstable isotope like O[18], calc won't provide any more O
        """
        cdef double ML, MR, delta
        delta = self.rtol*M
        M -= base_group.mass()
        ML = M-delta
        MR = M+delta

        cdef unordered_map[int32_t, int32_t] base_isotope
        cdef pair[pair[int32_t, int32_t], int32_t] iso_iter
        for iso_iter in base_group.isotopes:
            if base_isotope.count(iso_iter.first.first) == 0 or base_isotope[iso_iter.first.first] < iso_iter.first.second:
                base_isotope[iso_iter.first.first] = iso_iter.second

        cdef deque[State] isotopes
        cdef State state

        cdef int32_t top, length, i, numMin

        cdef pair[double, pair[int32_t, int32_t]] iterator
        for iterator in self.calcedIsotopes:
            if base_isotope.count(iterator.second.first) > 0 and (iterator.second.second == 0 or iterator.second.second < base_isotope[iterator.second.first]):
                continue
            state = State(isotope = iterator.second, num = 0, mass = iterator.first, massSum = 0, numMax = 0)
            isotopes.push_front(state)
        
        cdef list ret = list()

        top = 0
        length = isotopes.size() - 1
        cdef State* ref
        cdef double mass
        self.calcStateNum(isotopes[0], MR)
        while True:
            # printState(isotopes, top)
            ref = &isotopes[top]
            if deref(ref).num > deref(ref).numMax:
                if predec(top) < 0:
                    break
                incState(isotopes[top])
            else:
                ref = &isotopes[preinc(top)]
                deref(ref).num = 0
                deref(ref).massSum = isotopes[top-1].massSum
                self.calcStateNum(deref(ref), MR)
                if top == length:
                    numMin = max(<int>ceil((ML-deref(ref).massSum)/deref(ref).mass), 0)

                    # print(numMin, deref(ref).numMax)
                    
                    for i in range(numMin,deref(ref).numMax+1):
                        deref(ref).num = i
                        # print(i)
                        ret.append(isotopes2formula(isotopes) + base_group)
                
                    # print('exit')

                    incState(isotopes[predec(top)])
        return ret

    def get(self, double M, Formula base_group=Formula.__new__(Formula)):
        if base_group.isIsotope:
            raise ValueError("Not support for base_group contains unstable isotope")
        cdef Formula zero_formula = Formula.__new__(Formula), tmp

        cdef bool find
        cdef int32_t i, num
        cdef vector[pair[int32_t, int32_t]] isotopes
        cdef pair[int32_t, int32_t] isotope
        cdef list space = [], axis
        cdef tuple point
        cdef set result = set()
        cdef pair[pair[int32_t, int32_t], int32_t] iterator
        for iterator in self.isotopeMaximum:
            if iterator.first.second == 0 or base_group.elements.count(iterator.first.first) == 0:
                continue
            isotopes.push_back(iterator.first)
            axis = []
            for i in range(min(base_group.elements[iterator.first.first], iterator.second)+1):
                axis.append(i)
            space.append(axis)

        for point in product(*space):
            tmp = base_group.copy()
            find = True
            for i in range(len(point)):
                num = point[i]
                isotope = isotopes[i]
                if num > tmp.getE(isotope.first) - tmp.getI(isotope.first, 0):
                    find = False
                    break
                tmp.setI(isotope.first, isotope.second, num)
            if find:
                # print(tmp)
                result.update(self.get_direct(M, tmp))
        return list(result)
        

cdef void printState(deque[State]& states, int top):
    print(end=f'{top}, mass:{states[top].massSum}, {states[top].numMax}:')
    for state in states:
        if top == -1:
            break
        top-=1
        print(end=element2str(state.isotope)+str(state.num))

    print()