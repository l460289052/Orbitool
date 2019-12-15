import math
import re
from bintrees import FastRBTree
from pyteomics import mass


class calcFormula(object):
    def __init__(self):
        # key: left of a interval. value: right of a interval
        self._cover_RBTree = FastRBTree()
        # key: mass. value: formula
        self._calced_RBTree = FastRBTree()

        self.errppm = 1e-6

        self.elements = ['C', 'H', 'O', 'N', 'S', 'Na']
        self.elements_set = set(self.elements)
        self.isotopes = ['C[13]', 'O[18]', 'S[34]']
        self.isotopes_set = set(self.isotopes)
        self.isotopes_map = {'C[13]': 'C', 'O[18]': 'O', 'S[34]': 'S'}

        self.constrain = \ 
            {'C': (0, 20), 'H': (0, 40), 'O': (1, 10), 'N': (0, 3), 'S': (0, 1),
             'C[13]': (0, 3), 'O[18]': (0, 2),
             'DBE': (0, 8),
              'OCratioMax': 3, 'ONratioMax': 3, 'OSratioMax': 4,
              'NitrogenRule': False, charge = -1}

    def calc(self, M: float, queue=None) -> List[Ion]:
        """
        @M : mass
        @queue : communicate cross process
        """

        (Mmin, Mmax) = (M / (1 + self.errppm), M / (1 - self.errppm))

        if self._covered(Mmin, Mmax):
            if queue is not None:
                queue.put(((Mmin, Mmax), []))
            return self._calced_get(M)

        ans = []
        isotope = []
        Hmass = mass.calculate_mass(formula='H')
        Nmass = mass.calculate_mass(formula='N')
        Omass = mass.calculate_mass(formula='O')
        formula = Ion()
        Crange = range(
            max(0, self['C'][0]),
            min(int(math.floor(M/12)), self['C'][1])+1)
        # 改成递归的形式，使用栈
        for Cnum in Crange:
            formula['C'] = Cnum
            for Nnum in range(self['Nmin'], self['Nmax'] + 1):
                formula['N'] = Nnum
                if formula.mass() > Mmax:
                    break
                for Snum in range(self['Smin'], self['Smax'] + 1):
                    formula['S'] = Snum
                    m = formula.mass()
                    Orange = range(
                        max(self['Omin'],
                            int(math.ceil((Mmin - m - Hmass * formula.Hmax()) / Omass))),
                        min(self['Omax'],
                            self['OCratioMax'] * Cnum + self['ONratioMax'] *
                            Nnum + self['OSratioMax'] * Snum,
                            int(math.floor((Mmax - m - Hmass*formula.Hmin()) / Omass)))
                        + 1)

                    for Onum in Orange:
                        formula['O'] = Onum
                        m = formula.mass()
                        Hmin = max(
                            formula.Hmin(),
                            self['Hmin'],
                            int(math.ceil((Mmin - m) / Hmass)))
                        Hmax = min(
                            formula.Hmax(),
                            self['Hmax'],
                            int(math.floor((Mmax - m) / Hmass)))
                        formula['H'] = Hmax
                        if formula.DBE() > self['DBEmax']:
                            break
                        for Hnum in range(Hmin, Hmax + 1):
                            formula['H'] = Hnum
                            if formula.DBE() < self['DBEmin']:
                                break
                            if formula.DBE() > self['DBEmax'] or self['NitrogenRule'] and (formula['H'] + formula['N']) % 2 != 1:
                                continue
                            f_copy = formula.copy()
                            ans.append(f_copy)
                            self._calced_insert(f_copy)

                            isotope.extend(
                                self._find_and_insert_isotope(formula))

                        formula['H'] = 0
                    formula['O'] = 0
                formula['S'] = 0

        self._cover(Mmin, Mmax)
        if queue is not None:
            isotope.extend(ans)
            queue.put(((Mmin, Mmax), isotope))
        return ans

    def _covered(self, left, right):
        try:
            l, r = self._cover_RBTree.floor_item(left)
            return right <= r
        except KeyError:
            return False

    def _cover(self, left, right):
        if self._covered(left, right):
            return
        (min_l, max_r) = (left, left)
        try:
            l, r = self._cover_RBTree.floor_item(left)
            if r > min_l:
                self._cover_RBTree.remove(l)
                min_l = l
        except KeyError:
            pass
        try:
            l, r = self._cover_RBTree.ceiling_item(left)
            while l < right:
                self._cover_RBTree.remove(l)
                max_r = r
                l, r = self._cover_RBTree.ceiling_item(left)
        except KeyError:
            pass
        if max_r < right:
            max_r = right
        self._cover_RBTree.insert(min_l, max_r)

    def _calced_insert(self, formula):
        m = formula.mass()
        e = False
        try:
            mm, f = self._calced_RBTree.floor_item(m)
            if formula == f:
                e = True
        except KeyError:
            pass
        try:
            mm, f = self._calced_RBTree.ceiling_item(m)
            if formula == f:
                e = True
        except KeyError:
            pass
        if not e:
            self._calced_RBTree.insert(m, formula)

    def _calced_get(self, m):
        ans = []
        mi = m/(1+self.errppm)
        ma = m/(1-self.errppm)
        try:
            mm, f = self._calced_RBTree.floor_item(m)
            while mm > mi:
                ans.append(f)
                mm, f = self._calced_RBTree.prev_item(mm)
        except KeyError:
            pass
        try:
            mm, f = self._calced_RBTree.ceiling_item(m)
            while mm < ma:
                ans.append(f)
                mm, f = self._calced_RBTree.succ_item(mm)
        except KeyError:
            pass
        return ans

    def _find_and_insert_isotope(self, formula):
        ans = []
        for isotope in _isotopes:
            origin_e = _isotopes_map[isotope]
            if not origin_e in formula:
                continue
            isomax = None
            if isotope+'max' in self.restriction:
                isomax = min(
                    self.restriction[isotope+'max'], formula[origin_e])
            else:
                isomax = formula[origin_e]
            for isonum in range(1, isomax + 1):
                f = formula.copy()
                f[origin_e] = formula[origin_e] - isonum
                f[isotope] = isonum
                self._calced_insert(f)
                ans.append(f)
        return ans

    def __setitem__(self, key, value):
        if self.restriction[key] == value:
            return
        if type(value) not in {int, bool}:
            raise ValueError('number constrain should be integer')
        self._cover_RBTree.clear()
        self._calced_RBTree.clear()
        self.restriction[key] = value

    def __getitem__(self, key):
        return self.restriction[key]


if __name__ == '__main__':
    calc = calcFormula()
    calc.errppm = 2e-6
    l = calc.calc(mass.calculate_mass(formula="HN2O6")+0.0005486)
    for ll in l:
        print(str(ll), mass.calculate_mass(
            formula=str(ll)))
    samples = ['HNO3NO3-', 'C6H3O2NNO3-', 'C6H5O3NNO3-',
               'C6H4O5N2NO3-', 'C8H12O10N2NO3-', 'C10H17O10N3NO3-']
    for s in samples:
        formula = Ion(s)
        print(s, str(formula))

    # a = Formula('C11C[13]2H14O5-')
    # print(a.relativeAbundance())
