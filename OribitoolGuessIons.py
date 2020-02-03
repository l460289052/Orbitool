import math
import re

from sortedcontainers import SortedDict
from pyteomics import mass

from OribitoolFormula import Formula

p_elements = ['C', 'H', 'O', 'N', 'Na']
p_isotopes = ['C[13]', 'O[18]']
n_elements = ['C', 'H', 'O', 'N', 'S']
n_isotopes = ['C[13]', 'O[18]', 'S[34]']


class IonCalculator(object):
    def __init__(self):
        # key: left value of a interval. value: right of a interval
        self._cover_ = SortedDict()
        # key: mass. value: formula
        self._calced_ = SortedDict()

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
        self._cover_.clear()
        self._calced_.clear()

    def _covered(self, left, right):
        index = self._cover_.bisect_left(left)
        if index > 0:
            return right <= self._cover_.peekitem(index - 1)[1]
        return False

    def _cover(self, left, right):
        if self._covered(left, right):
            return
        cover = self._cover_
        min_l = left
        max_r = left
        index = cover.bisect_left(left) - 1
        if index >= 0:
            l, r = cover.peekitem(index)
            if r > min_l:
                cover.popitem(index)
                min_l = l

        while True:
            index = cover.bisect_right(left)
            if index < len(cover):
                l, r = cover.peekitem(index)
                if l < right:
                    cover.popitem(index)
                    max_r = r
                else:
                    break
            else:
                break
        if max_r < right:
            max_r = right
        cover[min_l] = max_r

    def _calced_insert(self, ion):
        m = ion.mass()
        calced = self._calced_
        index = calced.bisect_left(m)
        if index > 0:
            mm, f = calced.peekitem(index - 1)
            if ion == f:
                return
        if index < len(calced):
            mm, f = calced.peekitem(index)
            if ion == f:
                return
        calced[m]=ion
            

    def _calced_get(self, m):
        mi = m / (1 + self.errppm)
        ma = m / (1 - self.errppm)
        calced=self._calced_
        return [calced[mm] for mm in calced.irange(mi, ma)]
        

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
        self.clear()
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
        self._calced_=SortedDict()

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
