# -*- coding: utf-8 -*-
import math
import re

from sortedcontainers import SortedDict, SortedSet
from pyteomics import mass
import numpy as np

import OribitoolFormula
from OribitoolFormula import Formula

p_elements = ['N', 'Na']
p_isotopes = ['C[13]', 'O[18]']
n_elements = ['N', 'S']
n_isotopes = ['C[13]', 'O[18]', 'S[34]']


class IonCalculator(object):
    def __init__(self):
        # key: mass. value: formula
        self._calced_ = SortedDict()

        self.errppm = 1e-6

        self.constrain = \
            {'elements': n_elements, 'isotopes': n_isotopes,
             'C[13]': (0, 3), 'O[18]': (0, 2), 'S[34]': (0, 1),
             'DBE': (0, 8),
             'OCRatioMax': 3, 'ONRatioMax': 3, 'OSRatioMax': 4, 'charge': -1}

    def initialize(self):
        self._calced_.clear()
        nist = mass.nist_mass

        elements = self['elements']
        elementsParas = OribitoolFormula.elements
        f = Formula(charge=self['charge'])
        stop = len(elements) - 1
        for Cnum in range(elementsParas['C'][0], elementsParas['C'][1] + 1):
            f['C'] = Cnum
            para = elementsParas['C']
            minO = Cnum * para[5]
            maxO = Cnum * para[6]
            if self['charge'] == -1:
                minH = -1
                maxH = -1
            else:  # charge == 1
                minH = 0
                maxH = 0
            minH += OribitoolFormula.CHmin[Cnum]
            maxH += Cnum*para[4]

            current = 0
            elementNums = [0]
            elementPara = [elementsParas[elements[0]]]
            elementMax = []
            while current >= 0:
                if elementNums[-1] > elementPara[-1][1]:
                    num = elementNums.pop()
                    para = elementPara.pop()
                    minO -= num * para[5]
                    maxO -= num * para[6]
                    minH -= num * para[3]
                    maxH -= num * para[4]
                    f[elements[current]] = 0
                    current -= 1
                    if current >= 0:
                        elementNums[-1] += 1
                        f[elements[current]] += 1
                        para = elementPara[-1]
                        minO += para[5]
                        maxO += para[6]
                        minH += para[3]
                        maxH += para[4]
                elif current < stop:
                    current += 1
                    e = elements[current]
                    para = elementsParas[e]
                    num = para[0]
                    minO += num * para[5]
                    maxO += num * para[6]
                    minH += num * para[3]
                    maxH += num * para[4]
                    f[e] = num
                    elementNums.append(num)
                    elementPara.append(para)
                else:
                    # if minH != f.Hmin() or maxH != f.Hmax() or minO != f.Omin() or maxO != f.Omax():
                    #     print('error')
                    Orange = range(max(elementsParas['O'][0], minO), min(
                        elementsParas['O'][1], maxO)+1)
                    Hrange = range(max(elementsParas['H'][0], minH), min(
                        elementsParas['H'][1], maxH) + 1)
                    if len(Hrange) > 0:
                        for Onum in Orange:
                            f['O'] = Onum
                            for Hnum in Hrange:
                                f['H'] = Hnum
                                self._calced_insert(f.copy())
                                self._find_and_insert_isotope(f)
                        f['O'] = 0
                        f['H'] = 0
                    elementNums[-1] += 1
                    f[elements[-1]] += 1
                    para = elementPara[-1]
                    minO += para[5]
                    maxO += para[6]
                    minH += para[3]
                    maxH += para[4]

    def calc(self, M: float, queue=None) -> list:
        """
        @M : mass
        @queue : communicate cross process
        """

        return self._calced_get(M)

    def clear(self):
        self.Ccovered = None
        self.CMRange = None
        self._calced_.clear()

    def _calced_insert(self, ion, m=None):
        if m is None:
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
        calced[m] = ion

    def _calced_get(self, m):
        mi = m / (1 + self.errppm)
        ma = m / (1 - self.errppm)
        calced = self._calced_
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
            if isotope in self.constrain:
                isomax = min(
                    self.constrain[isotope][1], ion[origin_e])
            else:
                isomax = ion[origin_e]
            for isonum in range(1, isomax + 1):
                f = ion.copy()
                f[origin_e] = ion[origin_e] - isonum
                f[isotope] = isonum
                self._calced_insert(f)
                ans.append(f)
        return ans

    def __getitem__(self, key):
        return self.constrain[key]
