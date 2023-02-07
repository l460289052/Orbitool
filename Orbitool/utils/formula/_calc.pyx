# distutils: language = c++
# cython: language_level = 3

from cython.operator cimport (
    dereference as deref, preincrement as preinc, predecrement as predec,
    postdecrement as postdec, postincrement as postinc)
from libc.stdint cimport int32_t
from libc.math cimport fabs, remainder, ceil, floor, round as fround
from libcpp.stack cimport stack
from libcpp cimport bool

from ._element cimport(
    elements as e_elements, elementMass, elementMassDist, elementMassNum,
    str2element, element2str, int_pair, dou_pair) 
from ._formula cimport (
    Formula, int_map, ints_pair, ints_map, _elements_mass,
    _mass_isotopes_mass)

cdef double eps = 1e-9

cdef int EIndex = 0, HIndex = 1, CIndex = 6, OIndex = 8

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
    def __init__(
            self, double rtol, double DBEMin, double DBEMax,
            bool nitrogen_rule, int32_t global_limit, bool dbe_limit, 
            double H_max_mass, dict element_states, list isotope_nums, 
            bool debug):
        self.rtol = rtol
        self.DBEMin = DBEMin
        self.DBEMax = DBEMax
        self.nitrogen_rule = nitrogen_rule
        self.global_limit = global_limit
        self.dbe_limit = dbe_limit
        self.H_max_mass = H_max_mass

        for key, state in element_states.items():
            self.element_states[str2element(key).first] = State(
                DBE2=state.DBE2, OMin=state.OMin, OMax=state.OMax, HMin=state.HMin, HMax=state.HMax)

        for i_num in isotope_nums:
            self.isotope_nums.push_back(IsotopeNum(
                e=str2element(i_num.element).first, i_num=i_num.i_num, i_min=i_num.i_min, i_max=i_num.i_max,
                e_min=i_num.e_min, e_max=i_num.e_max, global_limit=i_num.global_limit))
    
    def get(self, double M, int32_t charge):
        cdef double delta = self.rtol * M, ML, MR
        ML = M - delta
        MR = M + delta

        cdef stack[State] states
        cdef stack[NumState] num_states
        cdef list formulas = [Formula(charge=charge)]

        states.push(State(DBE2=0, OMin=0, OMax=0, HMin=0, HMax=0))
        _state_add(states.top(), self.element_states[EIndex], -charge)
        _state_add(states.top(), self.element_states[HIndex], -2)
        num_states.push(NumState(
            e=0, current=-charge, e_current=-charge, max=-charge,
            global_limit_sum=0, mass=elementMass[0]*-charge))

        cdef IsotopeNum *e_num
        cdef NumState *ns, *last_ns
        cdef State *s, *last_s, *e_s
        cdef Formula f, last_f
        cdef double e_mass, mi, ma
        cdef int32_t e_current, global_limit_sum, mi_int, ma_int
        cdef int32_t cur = 0, TAIL = self.isotope_nums.size() - 1
        cdef list ret = []

        while True:
            ns = &num_states.top()
            if ns.current <= ns.max:
                last_ns = &num_states.top()
                last_s = &states.top()
                last_f = formulas[-1]
                # print(last_f)
                e_num = &self.isotope_nums[cur]
                e_s = &self.element_states[e_num.e]
                e_mass = elementMassDist[e_num.e][e_num.i_num].first
                mi = e_num.i_min
                if cur == TAIL or self.isotope_nums[cur+1].e != e_num.e:
                    if last_ns.e == e_num.e:
                        mi = max(mi, e_num.e_min - last_ns.e_current)
                    else:
                        mi = max(mi, e_num.e_min)
                    if self.dbe_limit:
                        if e_num.e == OIndex:
                            mi = max(
                                mi, last_s.OMin,
                                (ML - last_ns.mass - self.H_max_mass * last_s.HMax) / e_mass)
                        elif e_num.e == HIndex:
                            mi = max(
                                mi, last_s.HMin,
                                (self.DBEMax*2 - last_s.DBE2) / e_s.DBE2)
                            
                    if cur == TAIL:
                        mi = max(mi, (ML - last_ns.mass) / e_mass)
                mi = ceil(mi)
                mi_int = <int32_t> mi

                ma = e_num.i_max
                if last_ns.e == e_num.e:
                    ma = min(ma, e_num.e_max - last_ns.e_current)
                    e_current = last_ns.e_current + mi_int
                else:
                    e_current = mi_int
                if self.dbe_limit:
                    if e_num.e == OIndex:
                        ma = min(ma, last_s.OMax)
                    elif e_num.e == HIndex:
                        ma = min(
                            ma, last_s.HMax,
                            (self.DBEMin*2 - last_s.DBE2) / e_s.DBE2)
                if e_num.global_limit:
                    global_limit_sum = last_ns.global_limit_sum + mi_int
                    ma = min(ma, self.global_limit - last_ns.global_limit_sum)
                else:
                    global_limit_sum = last_ns.global_limit_sum
                ma = min(ma, (MR - last_ns.mass) / e_mass)
                ma = floor(ma)
                ma_int = <int32_t>ma

                f = last_f.copy()
                if cur != TAIL:
                    num_states.push(NumState(
                        e=e_num.e, current=mi_int, max=ma_int,
                        e_current=e_current, global_limit_sum=global_limit_sum,
                        mass=last_ns.mass + mi*e_mass))
                    states.push(deref(last_s))
                    _state_add(states.top(), deref(e_s), mi_int)
                    f.addEI(e_num.e, e_num.i_num, mi_int)
                    formulas.append(f)
                    cur += 1
                    continue
                else:
                    f.addEI(e_num.e, e_num.i_num, mi_int)
                    if self.nitrogen_rule:
                        DBE2 = last_s.DBE2 + mi_int * e_s.DBE2
                        for _ in range(mi_int, ma_int + 1) :
                            if fabs(fround(DBE2)-DBE2) < eps and self.check(f, ML, MR, charge):
                                ret.append(f.copy())
                            DBE2 += e_s.DBE2
                            f.addEI(e_num.e, e_num.i_num, 1)
                    else:
                        for _ in range(mi_int, ma_int + 1):
                            if self.check(f, ML, MR, charge):
                                ret.append(f.copy())
                            f.addEI(e_num.e, e_num.i_num, 1)

            else:
                cur -= 1
                if cur == 0:
                    break
                num_states.pop()
                states.pop()
                formulas.pop()
            
            ns = &num_states.top()
            s = &states.top()
            e_num = &self.isotope_nums[cur - 1]
            e_s = &self.element_states[e_num.e]
            ns.current += 1
            ns.e_current += 1
            ns.mass += elementMassDist[e_num.e][e_num.i_num].first
            if e_num.global_limit:
                ns.global_limit_sum += 1
            _state_inc(deref(s), deref(e_s))

            f = formulas[-1]
            f.addEI(e_num.e, e_num.i_num, 1)

        return ret

    cpdef bool check(self, Formula f, double ml, double mr, double charge):
        if not ml <= f.mass() <= mr:
            return False
        if fabs(-f.getE(EIndex) - charge) > eps:
            return False
        cdef State s = State(DBE2=0, OMin=0, OMax=0, HMin=0, HMax=0)
        _state_add(s, self.element_states[HIndex], -2)
        cdef int_pair iter
        for int_pair in f.elements:
            _state_add(s, self.element_states[int_pair.first], int_pair.second)
        if self.dbe_limit:
            if not s.OMin <= 0 <= s.OMax:
                return False
            if not s.HMin <= 0 <= s.HMax:
                return False
            if not self.DBEMin <= s.DBE2 / 2 <= self.DBEMax:
                return False
        return True


