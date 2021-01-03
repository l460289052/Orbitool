# distutils: language = c++
# cython: language_level = 3

from cpython cimport *
from cython.operator cimport dereference as deref, preincrement as preinc,\
     postincrement as postinc, predecrement as predec, postdecrement as postdec
from libcpp.vector cimport vector
from libcpp.deque cimport deque
from libcpp.string cimport string
from libcpp.list cimport list as cpplist
from libcpp.map cimport map
from libcpp.stack cimport stack
from libcpp.unordered_set cimport unordered_set
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair
from libcpp cimport bool
from libc.math cimport fabs, ceil, floor, remainder, fabs

from ._element cimport _factor, _andfactor, elements, elementMass,\
     elementMassNum, elementMassDist, elementNumMap, elementParasMap, CHmin, \
     encodeIsotope, decodeIsotope, str2element, element2str, str2code, code2str #, isotopeNumMap

from ._formula cimport _elements_mass, _elements_DBE, _elements_Omin,\
     _elements_Omax, _elements_Hmin, _elements_Hmax, _elements_eq, _mass_isotopes_mass,\
     _elements_isotopes_mass, Formula

cdef int Hindex = 1
cdef int Cindex = 6
cdef int Oindex = 8

cdef struct State:
    double DBE2, Omin, Omax, Hmin, Hmax

cdef void _state_inc(State& state, vector[double]& para):
    state.DBE2+=para[0] # couldn't create c++ reference
    state.Hmin+=para[1]
    state.Hmax+=para[2]
    state.Omin+=para[3]
    state.Omax+=para[4]

cdef void _state_dec(State& state, vector[double]& para):
    state.DBE2-=para[0]
    state.Hmin-=para[1]
    state.Hmax-=para[2]
    state.Omin-=para[3]
    state.Omax-=para[4]

cdef void _state_add(State& state, vector[double]& para, int num):
    state.DBE2+=para[0]*num
    state.Hmin+=para[1]*num
    state.Hmax+=para[2]*num
    state.Omin+=para[3]*num
    state.Omax+=para[4]*num

cdef double eps = 1e-9

cdef class BaseCalculator:
    def __init__(self):
        self.ppm = 1e-6
        self.charge = -1


cdef class IonCalculator(BaseCalculator):
    def __init__(self):
        BaseCalculator.__init__(self)
        self.calcedElements.push_back(Cindex)
        self.calcedElements.push_back(Hindex)
        self.calcedElements.push_back(Oindex)
        self.DBEmin = 0
        self.DBEmax = 8
        self.Mmin = 50
        self.Mmax = 750
        self.nitrogenRule = False

    def setEI(self, str key, bool use = True):
        cdef cpplist[int] *clist
        cdef cpplist[int].iterator it
        cdef int index, m, i, j
        str2element(key, &index, &m)
        if m == 0 or m == elementMassNum[index]:
            if index == Hindex or index == Cindex or index == Oindex:
                raise KeyError('cannot enable or disable C, H, O')
            clist = &self.calcedElements
        else:
            index = encodeIsotope(index, m)
            clist = &self.calcedIsotopes

        cdef bool has = False
        it = clist.begin()
        while it!=clist.end():
            if deref(it) == index:
                has = True
                break
            preinc(it)
        if use:
            if not has:
                clist.push_back(index)
        elif has:
            clist.erase(it)


    def getElements(self):
        cdef list e = list()
        cdef int i
        for i in self.calcedElements:
            e.append(elements[ i ])
        return e

    def getIsotopes(self):
        cdef list e = list()
        cdef int i, index, m
        for i in self.calcedIsotopes:
            decodeIsotope(i, &index, &m)
            e.append( f"{elements[index]}[{m}]" )
        return e

    cdef bool iscovered(self, double l, double r):
        cdef map[double, double].iterator it = self.mcover.upper_bound(l+eps)
        if it==self.mcover.begin():
            return False
        return r <= deref(predec(it)).second + eps

    cdef void cover(self, double l, double r):
        cdef map[double, double].iterator it
        cdef double ll=l, rr=l
        l+=eps
        it = self.mcover.upper_bound(l)
        if it!=self.mcover.begin():
            if deref(predec(it)).second>ll:
                if deref(it).second>r:
                    return
                ll=deref(it).first
        # c98 standard
                self.mcover.erase(it)
                it=self.mcover.upper_bound(l)
            else:
                preinc(it)
        while it!=self.mcover.end() and deref(it).first<r:
            rr=deref(it).second
            self.mcover.erase(it)
            it=self.mcover.upper_bound(l)
        # c11 standard
        #         it=self.mcover.erase(it)
        #     else:
        #         preinc(it)
        # while it!=self.mcover.end() and deref(it).first<r:
        #     rr=deref(it).second
        #     it=self.mcover.erase(it)
        if rr<r:
            rr=r
        self.mcover.insert(it, pair[double, double](ll, rr))
    
    cpdef void calc(self, double _Mmin = -1, double _Mmax = -1):
        cdef double ML = self.Mmin
        cdef double MR = self.Mmax
        if _Mmin>0 and _Mmax>0:
            ML = _Mmin
            MR = _Mmax
        else:
            self.clear()
        if self.iscovered(ML, MR):
            return
        cdef double DBE2min = self.DBEmin*2
        cdef double DBE2max = self.DBEmax*2

        cdef Formula f = Formula.__new__(Formula)
        f.charge = self.charge

        cdef int Cnum, Onum, Hnum, num, index, Cmin, Cmax, Omax, Hmax, numMax, step
        cdef cpplist[int] elements
        cdef cpplist[int].iterator eit
        cdef stack[int] elementNum, elementMax
        cdef stack[double] emass
        cdef double mass
        cdef bool nitrogenRule = self.nitrogenRule
        if nitrogenRule:
            step = 2
        else:
            step = 1

        elements.push_back(Cindex)
        for num in self.calcedElements:
            if num !=Hindex and num!=Cindex and num!=Oindex:
                elements.push_back(num)

        cdef State state
        Cmin = elementNumMap[Cindex][0]
        Cmax = min(<int>(MR/elementMass[Cindex]), elementNumMap[Cindex][1])
        for Cnum in range(Cmin, Cmax+1):
            f.setE(Cindex, Cnum)
            state = State(DBE2=f.DBE()*2,Omin=f.Omin(), Omax=f.Omax(),Hmin=f.Hmin(),Hmax=f.Hmax())
            elementNum.push(Cnum)
            elementMax.push(Cnum)
            emass.push(f.mass())
            eit = elements.begin()
            while True:
                # print(str(f), elementNum)
                if elementNum.top() > elementMax.top():
                    index = deref(eit)
                    _state_add(state, elementParasMap[index], -elementNum.top())
                    elementNum.pop()
                    elementMax.pop()
                    emass.pop()

                    f.setE(deref(postdec(eit)),0) # *eit--
                elif preinc(eit)!=elements.end():
                    index = deref(eit)
                    num = elementNumMap[index][0]
                    elementNum.push(num)
                    numMax = min(elementNumMap[index][1],<int>((MR - emass.top())/elementMass[index]))
                    elementMax.push(numMax)
                    if num>0:
                        _state_add(state, elementParasMap[index], num)
                        emass.push(emass.top()+elementMass[index]*num)
                    else:
                        emass.push(emass.top())
                    f.setE(index, num)
                    continue
                else:
                    mass=emass.top()
                    Onum=max(elementNumMap[Oindex][0], <int>max(state.Omin, ceil((ML-mass-elementMass[Hindex]*state.Hmax)/elementMass[Oindex])))
                    Omax=min(elementNumMap[Oindex][1], <int>min(state.Omax, (MR-mass-elementMass[Hindex]*state.Hmin)/elementMass[Oindex]))
                    if Onum<=Omax:
                        # print(f)
                        # print(state.DBE2, f.DBE())
                        # print(state.Hmin, f.Hmin())
                        # print(state.Hmax, f.Hmax())
                        # print(state.Omin, f.Omin())
                        # print(state.Omax, f.Omax())
                        # print(mass, f.mass())

                        mass+=elementMass[Oindex]*Onum
                        while Onum<=Omax:
                            f.setE(Oindex,Onum)
                            # O can't affct DBE and Hnum, so don't change state 
                            Hnum=max(elementNumMap[Hindex][0], <int>ceil(max(state.Hmin, (ML-mass)/elementMass[Hindex], (DBE2max-state.DBE2)/elementParasMap[Hindex][0])))
                            Hmax=min(elementNumMap[Hindex][1], <int>min(state.Hmax, (MR-mass)/elementMass[Hindex], (DBE2min-state.DBE2)/elementParasMap[Hindex][0]))
                            if nitrogenRule and fabs(remainder(state.DBE2+Hnum*elementParasMap[Hindex][0], 2.0))>eps:
                                preinc(Hnum)
                            
                            while Hnum<=Hmax:
                                f.setE(Hindex,Hnum)
                                mass = _elements_mass(f.elements)
                                self.insertElements(f.elements, mass)
                                self.insertIsotopes(f.elements, mass)
                                Hnum+=step
                            preinc(Onum)
                            mass+=elementMass[Oindex]
                    f.setE(Oindex,0)
                    f.setE(Hindex,0)
                    
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
                _state_inc(state, elementParasMap[index])
        self.cover(ML,MR)

        # print(self.isotopes.size())
        # cdef pair[double, pair[double, cpplist[pair[int, int]]]] isotope
        # for isotope in self.isotopes:
        #     print(isotope)

    def get(self, double M):
        cdef double ML, MR, delta
        delta = self.ppm*M
        ML=M-delta
        MR=M+delta
        
        if not self.iscovered(ML, MR):
            self.calc(ML, MR)

        cdef list ret = list() # List[Formula]
        if self.formulas.empty():
            return ret
        cdef map[double, unordered_map[int, int]].iterator fit1, fit2
        self.getFormula(ML, &fit1)
        self.getFormula(MR, &fit2)
        cdef Formula formula
        while fit1 != fit2:
            formula = Formula.__new__(Formula)
            formula.elements = deref(fit1).second
            ret.append(formula)
            preinc(fit1)
        cdef map[double, pair[double, cpplist[pair[int, int]]]].iterator iit1, iit2
        self.getIsotope(ML, &iit1)
        self.getIsotope(MR, &iit2)
        while iit1!=iit2:
            self.getFormula(deref(iit1).second.first, &fit1)
            formula = Formula.__new__(Formula)
            formula.elements = deref(fit1).second
            formula.isotopes = deref(iit1).second.second
            ret.append(formula)
            preinc(iit1)
        return ret

    cpdef clear(self):
        self.formulas.clear()
        self.isotopes.clear()
        self.mcover.clear()

    cdef bool getFormula(self, double& mass, map[double, unordered_map[int, int]].iterator* out):
        '''
        if return True, out will be the iterator pointing mass
        if return False, out will point the position to be added
        '''
        if self.formulas.empty():
            out[0] = self.formulas.end()
            return False
        out[0] = self.formulas.upper_bound(mass)
        if out[0] != self.formulas.end():
            if fabs(deref(out[0]).first-mass)<eps:
                return True
            elif out[0] == self.formulas.begin(): # begin and end will occur concurrently
                return False
        if fabs(deref(predec(out[0])).first-mass)<eps:
            return True
        else:
            preinc(out[0])
            return False

    cdef void insertElements(self, unordered_map[int, int]& elements, double mass = -1):
        if mass < 0:
            mass = _elements_mass(elements)
        cdef map[double, unordered_map[int, int]].iterator it
        if not self.getFormula(mass, &it):
            self.formulas.insert(it, pair[double, unordered_map[int, int]](mass, elements))
    
    cdef void insertIsotopes(self, unordered_map[int, int]& elements, double mass = -1):
        if mass < 0:
            mass = _elements_mass(elements)
        
        cdef int i, j, index, m
        cdef unordered_map[int, int].iterator it
        cdef cpplist[pair[int, int]] isotopes
        cdef double isomass
        for i in self.calcedIsotopes:
            decodeIsotope(i, &index, &m)
            it = elements.find(index)
            if it==elements.end():
                continue
            isotopes.clear()
            # double
            if deref(it).second > 1:
                isotopes.push_back(pair[int,int](index,(m<<_factor)+2))
                self.insertIsotope(mass, isotopes)
            # single
                isotopes.back().second = isotopes.back().second-1
            else:
                isotopes.push_back(pair[int,int](index,(m<<_factor)+1))
            self.insertIsotope(mass, isotopes)

            # multi(2)
            for j in self.calcedIsotopes:
                if i==j: 
                    break
                decodeIsotope(i, &index, &m)
                if elements.find(index)==elements.end():
                    continue
                isotopes.push_back(pair[int,int](index,(m<<_factor)+1))
                self.insertIsotope(mass, isotopes)
                isotopes.pop_back()


    cdef void insertIsotope(self, double& mass, cpplist[pair[int, int]]& isotopes):
        cdef map[double, pair[double, cpplist[pair[int, int]]]].iterator isoit
        isomass = _mass_isotopes_mass(mass, isotopes)
        if not self.getIsotope(isomass, &isoit):
            self.isotopes.insert(isoit, pair[double, pair[double, cpplist[pair[int, int]]]](isomass, pair[double, cpplist[pair[int, int]]](mass, isotopes)))


    cdef bool getIsotope(self, double& mass, map[double, pair[double, cpplist[pair[int, int]]]].iterator* out):
        '''
        if return True, out will be the iterator pointing mass
        if return False, out will point the position to be added
        '''
        if self.isotopes.empty():
            out[0] = self.isotopes.end()
            return False
        out[0] = self.isotopes.upper_bound(mass)
        if out[0] != self.isotopes.end():
            if fabs(deref(out[0]).first-mass)<eps:
                return True
            elif out[0] == self.isotopes.begin(): # begin and end will occur concurrently
                return False
        if fabs(deref(predec(out[0])).first-mass)<eps:
            return True
        else:
            preinc(out[0])
            return False
        
cdef pair[double, int] convert_isotopes2pair(int index, int m):
    if m == elementMassNum[index]:
        m = 0
    return pair[double, int]( elementMassDist[index][m].first,encodeIsotope(index, m))

cdef str convert_pair2str(pair[double, int] p):
    cdef int index, m
    decodeIsotope(p.second, &index, &m)
    return elements[index] if m ==0 else f"{elements[index]}[{m}]"

cdef void incForceState(ForceState*state):
    preinc(deref(state).num)
    deref(state).massSum=deref(state).massSum + deref(state).mass # += is not supported well in cython

cdef Formula isotopes2formula(deque[ForceState]&isotopes, int charge):
    cdef ForceState i
    cdef Formula f = Formula.__new__(Formula)
    for i in isotopes:
        f.addEI(i.isotope>>_factor, i.isotope&_andfactor, i.num)
    f.setE(0, -charge)
    # print(f)
    return f


cdef class ForceCalculator(BaseCalculator):
    def __init__(self):
        BaseCalculator.__init__(self)
        cdef int i
        cdef vector[int] l = [Cindex, Hindex, Oindex]
        for i in l:
            self.calcedIsotopes.insert(convert_isotopes2pair(i,0))
            self.isotopeMaximum.insert(pair[int, int](encodeIsotope(i, 0), 999))

    cdef map[double, int].iterator findIsotope(self, int code):
        cdef map[double, int].iterator iterator = self.calcedIsotopes.begin()
        while iterator!= self.calcedIsotopes.end():
            if deref(iterator).second == code:
                break
            preinc(iterator)
        return iterator

    cdef ForceCalculatorReturner strFindIsotope(self, str key):
        cdef int index, m, code
        str2element(key, &index, &m)
        if m == elementMassNum[index]:
            m = 0
        code = encodeIsotope(index, m)
        cdef map[double, int].iterator iterator = self.findIsotope(code)
        return ForceCalculatorReturner(iterator=iterator, index = index, m=m,code=code)

    cdef void calcForceStateNum(self, ForceState*state, double MR):
        cdef double mass = deref(state).massSum
        deref(state).numMax = min(<int>((MR-mass)/deref(state).mass), self.isotopeMaximum[deref(state).isotope])

    def __setitem__(self, str key, int value):
        cdef ForceCalculatorReturner returner = self.strFindIsotope(key)
        if returner.iterator == self.calcedIsotopes.end():
            if value > 0:
                self.calcedIsotopes.insert(convert_isotopes2pair(returner.index, returner.m))
                self.isotopeMaximum.insert(pair[int,int]((returner.code, value)))
        else:
            if value == 0:
                self.calcedIsotopes.erase(returner.iterator)
                self.isotopeMaximum.erase(returner.code)
            else:
                self.isotopeMaximum[returner.code] = value

    def __getitem__(self, str key):
        cdef ForceCalculatorReturner returner = self.strFindIsotope(key)
        if returner.iterator == self.calcedIsotopes.end():
            return 0
        return self.isotopeMaximum[returner.code]

    def getEI(self):
        cdef list ret = list()
        cdef pair[double, int] iterator
        for iterator in self.calcedIsotopes:
            ret.append(convert_pair2str(iterator))

        return ret


    def get(self, double M):
        M += self.charge*elementMass[0]
        cdef double ML, MR, delta
        delta = self.ppm *M
        ML = M - delta
        MR = M + delta
        # print(ML,MR)

        cdef deque[ForceState] isotopes
        cdef ForceState state
        cdef int index, m, top, length, i , numMin

        cdef pair[double, int] iterator
        for iterator in self.calcedIsotopes:
            state = ForceState(isotope=iterator.second, num = 0, mass = iterator.first, massSum = 0.0,numMax=0)
            isotopes.push_front(state)

        # for iso in isotopes:
        #     print(iso)

        cdef list ret = list()

        top = 0
        length = isotopes.size() - 1
        cdef ForceState* ref
        cdef double mass
        self.calcForceStateNum(&isotopes[0], MR)
        while True:
            # printState(isotopes, top)
            ref = &isotopes[top]
            if deref(ref).num > deref(ref).numMax:
                if predec(top) < 0:
                    break
                incForceState(&isotopes[top])
            else:
                ref = &isotopes[preinc(top)]
                deref(ref).num = 0
                deref(ref).massSum=isotopes[top-1].massSum
                self.calcForceStateNum(ref, MR)
                if top==length:
                    numMin = <int>ceil((ML-deref(ref).massSum)/deref(ref).mass)

                    # print(numMin, deref(ref).numMax)

                    for i in range(numMin,deref(ref).numMax+1):
                        deref(ref).num = i
                        # print(i)
                        ret.append(isotopes2formula(isotopes, self.charge)) # C10H[2]O[18]- bug

                    # print('exit')

                    incForceState(&isotopes[predec(top)])

        return ret

cdef void printState(deque[ForceState] states, int top):
    print(end=f'{top}, {states[top].massSum}, {states[top].numMax}:')
    for state in states:
        if top == -1:
            break
        top-=1
        print(convert_pair2str(pair[double,int]( state.mass, state.isotope))+str(state.num), end = '')

    print()