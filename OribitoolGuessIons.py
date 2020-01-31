import math
import re
from bintrees import FastRBTree
from pyteomics import mass

from OribitoolFormula import Formula

p_elements = ['C', 'H', 'O', 'N', 'Na']
p_isotopes = ['C[13]', 'O[18]']
n_elements = ['C', 'H', 'O', 'N', 'S']
n_isotopes = ['C[13]', 'O[18]', 'S[34]']


class IonCalculator(object):
    def __init__(self):
        # key: left of a interval. value: right of a interval
        self._cover_RBTree = FastRBTree()
        # key: mass. value: formula
        self._calced_RBTree = FastRBTree()

        self.errppm = 1e-6

        self._constrain = \
            {'elements': n_elements, 'isotopes': n_isotopes,
             'C': (0, 20), 'H': (0, 40), 'O': (1, 15), 'N': (0, 4), 'S': (0, 1), 'Na': (0, 1),
             'C[13]': (0, 3), 'O[18]': (0, 2), 'S[34]': (0, 1),
             'DBE': (0, 8),
             'OCRatioMax': 3, 'ONRatioMax': 3, 'OSRatioMax': 4,
             'NitrogenRule': False, 'charge': -1}

    def calc(self, M: float, queue=None) -> list:
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
        ion = Formula()
        ion.charge = self['charge']
        if self['charge'] == -1:
            Crange = range(
                max(0, self['C'][0]),
                min(int(math.floor(M/12)), self['C'][1])+1)
            for Cnum in Crange:
                ion['C'] = Cnum
                for Nnum in range(self['N'][0], self['N'][1] + 1):
                    ion['N'] = Nnum
                    if ion.mass() > Mmax:
                        break
                    for Snum in range(self['S'][0], self['S'][1] + 1):
                        ion['S'] = Snum
                        m = ion.mass()
                        Orange = range(
                            max(self['O'][0],
                                int(math.ceil((Mmin - m - Hmass * ion.Hmax()) / Omass))),
                            min(self['O'][1],
                                self['OCRatioMax'] * Cnum + self['ONRatioMax'] *
                                Nnum + self['OSRatioMax'] * Snum,
                                int(math.floor((Mmax - m - Hmass*ion.Hmin()) / Omass)))
                            + 1)

                        for Onum in Orange:
                            ion['O'] = Onum
                            m = ion.mass()
                            Hmin = max(
                                ion.Hmin(),
                                self['H'][0],
                                int(math.ceil((Mmin - m) / Hmass)))
                            Hmax = min(
                                ion.Hmax(),
                                self['H'][1],
                                int(math.floor((Mmax - m) / Hmass)))
                            ion['H'] = Hmax
                            if ion.DBE() > self['DBE'][1]:
                                break
                            for Hnum in range(Hmin, Hmax + 1):
                                ion['H'] = Hnum
                                if ion.DBE() < self['DBE'][0]:
                                    break
                                if ion.DBE() > self['DBE'][1] or self['NitrogenRule'] and (ion['H'] + ion['N']) % 2 != 1:
                                    continue
                                f_copy = ion.copy()
                                ans.append(f_copy)
                                self._calced_insert(f_copy)

                                isotope.extend(
                                    self._find_and_insert_isotope(ion))

                            ion['H'] = 0
                        ion['O'] = 0
                    ion['S'] = 0
                ion['N'] = 0
        elif self['charge'] == 1:
            Crange = range(
                max(0, self['C'][0]),
                min(int(math.floor(M/12)), self['C'][1])+1)
            for Cnum in Crange:
                ion['C'] = Cnum
                for Nnum in range(self['N'][0], self['N'][1] + 1):
                    ion['N'] = Nnum
                    if ion.mass() > Mmax:
                        break
                    for Nanum in range(self['Na'][0], self['Na'][1] + 1):
                        ion['Na'] = Nanum
                        m = ion.mass()
                        Orange = range(
                            max(self['O'][0],
                                int(math.ceil((Mmin - m - Hmass*ion.Hmax()) / Omass))),
                            min(self['O'][1],
                                self['OCRatioMax']*Cnum +
                                self['ONRatioMax']*Nnum,
                                int(math.floor((Mmax - m - Hmass*ion.Hmin()) / Omass)))
                            + 1)

                        for Onum in Orange:
                            ion['O'] = Onum
                            m = ion.mass()
                            Hmin = max(
                                ion.Hmin()-Nanum,
                                self['H'][0],
                                int(math.ceil((Mmin-m)/Hmass)))
                            Hmax = min(
                                ion.Hmax()-Nanum,
                                self['H'][1],
                                int(math.floor((Mmax-m)/Hmass)))
                            ion['H'] = Hmax
                            if ion.DBE() > self['DBE'][1]:
                                break
                            for Hnum in range(Hmin, Hmax + 1):
                                ion['H'] = Hnum
                                DBE = ion.DBE()
                                if DBE < self['DBE'][0]:
                                    break
                                if DBE > self['DBE'][1] or self['NitrogenRule'] and (Hnum+Nnum+Nanum) % 2 != 1:
                                    continue
                                i_copy = ion.copy()
                                ans.append(i_copy)
                                self._calced_insert(i_copy)

                                isotope.extend(
                                    self._find_and_insert_isotope(ion))
                            ion['H'] = 0
                        ion['O'] = 0
                    ion['Na'] = 0
                ion['N'] = 0

        self._cover(Mmin, Mmax)
        if queue is not None:
            isotope.extend(ans)
            queue.put(((Mmin, Mmax), isotope))
        return ans

    def clear(self):
        self._cover_RBTree.clear()
        self._calced_RBTree.clear()

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

    def _calced_insert(self, ion):
        m = ion.mass()
        e = False
        try:
            mm, f = self._calced_RBTree.floor_item(m)
            if ion == f:
                e = True
        except KeyError:
            pass
        try:
            mm, f = self._calced_RBTree.ceiling_item(m)
            if ion == f:
                e = True
        except KeyError:
            pass
        if not e:
            self._calced_RBTree.insert(m, ion)

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

    def _find_and_insert_isotope(self, ion):
        '''
        couldn't produce isotope ion like CC[13]H6O[18], whick have 2 different isotope
        '''
        ans = []
        for isotope in self['isotopes']:
            origin_e = re.match(r"[A-Z][a-z]{0,2}", isotope).group()
            if origin_e not in ion:
                continue
            isomax = None
            if isotope+'max' in self._constrain:
                isomax = min(
                    self._constrain[isotope][1], ion[origin_e])
            else:
                isomax = ion[origin_e]
            for isonum in range(1, isomax + 1):
                f = ion.copy()
                f[origin_e] = ion[origin_e] - isonum
                f[isotope] = isonum
                self._calced_insert(f)
                ans.append(f)
        return ans

    def __setitem__(self, key, value):
        if self._constrain[key] == value:
            return
        if len(self._cover_RBTree) > 0:
            self._cover_RBTree.clear()
        if len(self._calced_RBTree) > 0:
            self._calced_RBTree.clear()
        self._constrain[key] = value
        if key == 'charge':
            if value == 1:
                self._constrain['elements'] = n_elements
                self._constrain['isotopes'] = n_isotopes
            elif value == -1:
                self._constrain['elements'] = p_elements
                self._constrain['isotopes'] = p_isotopes

    def __getitem__(self, key):
        return self._constrain[key]


class IonCalculator_fulture(object):
    def __init__(self):
        self._calced_RBTree = FastRBTree()

        self.ppm = 1e-6
        # need to change
        self._constrain = \
            {'elements': n_elements, 'isotopes': n_isotopes,
             'C': (0, 20), 'H': (0, 40), 'O': (1, 15), 'N': (0, 4), 'S': (0, 1), 'Na': (0, 1),
             'C[13]': (0, 3), 'O[18]': (0, 2),
             'DBE': (0, 8),
             'OCRatioMax': 3, 'ONRatioMax': 3, 'OSRatioMax': 4, 'mass': (1, 999),
             'NitrogenRule': False, 'charge': -1}

    def init(self):
        pass
    '''
     有两种方案
     一、先枚举出所有可能的化学式，枚举时注意剪枝，再添加
     二、选取一些元素作为基础，记录可用的连接数，例如C(4)、N(3)等（括号内表示可用的连接数）
         ，再枚举其他类似官能团的东西，例如C(4)，则为C(4)+C(4)=C2(6)或C2(4)或C2(2)。
         其余还有SO3H(1)、N(3)、NO2(1)、X(1)（卤素）、O(2)、ONa(1)、O-(1)。最后以氢填充。注意查重。
    '''

    def calc(self):
        pass


if __name__ == '__main__':
    calcr = IonCalculator()
    calcr['charge'] = -1
    samples = ['HNO3NO3-', 'C6H3O2NNO3-', 'C6H5O3NNO3-',
               'C6H4O5N2NO3-', 'C8H12O10N2NO3-', 'C10H17O10N3NO3-']
    for s in samples:
        ion = Formula(s)
        print(ion, calcr.calc(ion.mass()))

    calcr['charge'] = 1
    for s in samples:
        ion = Formula(s)
        ion.charge = 1
        print(ion, calcr.calc(ion.mass()))
        # couldn't get C6H3O5N2+ for ion.Hmin()->4
