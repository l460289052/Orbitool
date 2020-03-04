# -*- coding: utf-8 -*-

import math
import re
from pyteomics import mass
import numpy as np
from collections import UserDict, OrderedDict

elementsOrder = ['C', 'H', 'O', 'N', 'S']
#          0    1    2      3      4      5      6
# element: min, max, 2*DBE, H min, H max, O min, O max
elements = dict([
    ('C', [0, 20, 2, '-', 2, 0, 3]),
    ('H', [0, 40, -1, -1, -1, 0, 0]),
    ('O', [0, 15, 0, 0, 0, -1, -1]),
    ('N', [0, 4, 1, -1, 1, 0, 3]),
    ('S', [0, 3, 0, 0, 0, 0, 4]),
    ('Li', [0, 3, -1, 0, 0, 0, 0]),
    ('Na', [0, 3, -1, 0, 0, 0, 0]),
    ('K', [0, 3, -1, 0, 0, 0, 0]),
    ('F', [0, 15, -1, -1, 0, 0, 0]),
    ('Cl', [0, 3, -1, -1, 0, 0, 3]),
    ('Br', [0, 3, -1, -1, 0, 0, 3]),
    ('I', [0, 3, -1, -1, 0, 0, 3]),
    ('P', [0, 4, 1, -1, 1, 0, 6]),
    ('Si', [0, 5, 2, 0, 2, 0, 3])])
    
def CHfunc(C):
	if C == 0:
		return 0
	elif C <= 2:
		return 4 
	elif C <= 6:
		return 6 
	elif C <= 10:
		return 8 
	elif C <= 16:
		return 10 
	elif C <= 24:
		return 12 
	elif C <= 32:
		return 14 
	elif C <= 42:
		return 16 
	elif C <= 54:
		return 18 
	else:
		return int(math.ceil(0.3 * C))

def getCHmin(elements):
    return np.array([CHfunc(c) for c in range(elements['C'][0],elements['C'][1]+1)], dtype = np.int)
	
CHmin = getCHmin(elements)

class Formula(UserDict):
    '''
    '''

    def __init__(self, formula: str = None, **kwargs):
        '''
        Formula('CC[13]H5O-')
        Formula({'C':1,'C[13]':1,'H':5,'O':1},charge=-1)
        Formula({'C':1,'C[13]':1,'H':5,'O':1,'charge'=-1})
        Formula(C=1,H=2,O=1,charge=-1)
        '''
        super().__init__()
        self.charge = 0
        self.isIsotope = False
        try:
            if type(formula) is str:
                if not re.fullmatch(r"([A-Z][a-z]{0,2}(\[\d+\])?\d*)+[-+]?", formula):
                    raise ValueError(str(formula))
                charge = formula[-1]
                if charge == '+':
                    self.charge = 1
                elif charge == '-':
                    self.charge = -1
                for match in re.finditer(r"([A-Z][a-z]{0,2})(\[\d+\])?(\d*)", formula):
                    e = match.group(1)
                    m = match.group(2)  # if dismatch, None
                    num = match.group(3)
                    self.addElement(e, m[1:-1] if m else None, num)
                return

            dic=kwargs.copy()
            if type(formula) is dict:
                for k, v in formula.items():
                    dic[k] = v

            for k, v in dic.items():
                match = re.fullmatch(r"([A-Z][a-z]{0,2})(\[\d+\])?", k)
                if match is not None:
                    e = match.group(1)
                    m = match.group(2)
                    self.addElement(e, m[1:-1]if m else None, v)
                elif k == 'charge':
                    self.charge = v
                else:
                    raise ValueError('wrong kwargs'+k)
        except ValueError as e:
            raise ValueError('wrong formula:' + str(e))

    def mass(self) -> float:
        return mass.calculate_mass(composition=self.data) - mass.nist_mass['e*'][0][0] * self.charge

    def addElement(self, element: str, m: str = None, num = None):
        '''
        if want to add 1 C[13]
        use `addElement('C','13',1)`
        '''
        # mass.nist_mass[element]-> dict(key(int):mass,value(tuple):(mass,abundance))
        # and mass.nist_mass[element][0] is unspecified isotopic state
        # print mass.nist_mass['C']
        # {0: (12.0, 1.0), 12: (12.0, 0.98938), 13: (13.0033548378, 0.01078), 14: (14.0032419894, 0.0)}
        if element not in mass.nist_mass:
            raise ValueError('unknown element:' + element)
        nist = mass.nist_mass[element]
        if m is not None:
            m = int(m)
            if int(round(nist[0][0])) != m:
                if m not in nist:
                    raise ValueError('unknown element:%s[%d]' % (element, m))
                self.isIsotope = True
                element += '[%d]' % (m)
        origin = super().__getitem__(element) if element in self else 0
        if type(num) is str:
            if len(num) > 0:
                num = int(num)
            else:
                num = None
        if num is not None:
            super().__setitem__(element, origin + num)
        else:
            super().__setitem__(element, origin + 1)

    def _isIsotope(self):
        for key in self.keys():
            if len(key) > 3:
                return True
        return False

    def DBE(self) -> float:
        """
        only count C N H
        """
        if self.isIsotope:
            return self.findOrigin().DBE()
        DBE_2 = 2.0
        for k, v in self.items():
            DBE_2 += v * elements[k][2]
        return DBE_2 / 2

    def Omin(self):
        if self.isIsotope:
            return self.findOrigin().Omin()
        ret = 0
        for k, v in self.items():
            ret += v * elements[k][5]
        # return ret
        return max(ret, elements['O'][0])

    def Omax(self):
        if self.isIsotope:
            return self.findOrigin().Omax()
        ret = 0
        for k, v in self.items():
            ret += v * elements[k][6]
        # return ret
        return min(ret, elements['O'][1])

    def Hmin(self):
        if self.isIsotope:
            return self.findOrigin().Hmin()
        ret = 0
        for k, v in self.items():
            if k == 'C':
                ret += int(CHmin[v])
            else:
                ret += v * elements[k][3]
        if self.charge == -1:
            ret -= 1
        # return ret
        return max(ret, elements['H'][0])
    
    def Hmax(self):
        if self.isIsotope:
            return self.findOrigin().Hmax()
        ret = 0
        for k, v in self.items():
            ret += v * elements[k][4]
        if self.charge == -1:
            ret -= 1
        # return ret
        return min(ret, elements['H'][1])

    def findOrigin(self):
        '''
        return non-istupe formula
        '''
        if not self.isIsotope:
            return self.copy()
        formula = self.copy()
        formula.isIsotope=False
        for e in self.keys():
            if len(e) > 3:
                match = re.match(r"[A-Z][a-z]{0,2}", e)
                origin = match.group()
                formula[origin] += self[e]
                formula.pop(e)
        return formula

    def relativeAbundance(self) -> float:
        """
        existing abundance, assume origin is 1
        """
        if not self.isIsotope:
            return 1
        return mass.isotopic_composition_abundance(formula=self.toStr(True, False)) /\
            mass.isotopic_composition_abundance(
                formula=self.findOrigin().toStr(True, False))

    def toStr(self, showProton: bool = False, withCharge: bool = True) -> str:
        s = []
        elements = list(self.keys())
        for e in elementsOrder:
            v = self[e]
            if v > 0:
                tmp = f"{e}[{int(round(mass.nist_mass[e][0][0]))}]" if showProton else e
                if v > 1:
                    tmp += str(v)
                s.append(tmp)
                elements.remove(e)
            if self.isIsotope:
                delete = []
                for isotope in elements:
                    if len(isotope) > 3 and isotope[0:len(e)] == e:
                        v = self[isotope]
                        if v > 0:
                            tmp = isotope
                            if v > 1:
                                tmp += str(v)
                            s.append(tmp)
                        delete.append(isotope)
                for d in delete:
                    elements.remove(d)
        for e in elements:
            v = self[e]
            if v > 0:
                tmp = f"{e}[{int(round(mass.nist_mass[e][0][0]))}]" if showProton and len(e) <= 3 else e
                if v > 1:
                    tmp += str(v)
                s.append(tmp)

        if withCharge:
            return ''.join(s) + ('+' if self.charge == 1 else '-' if self.charge ==-1 else '')
        return ''.join(s)

    def __setitem__(self, key, value):
        if type(value) != int:
            raise ValueError('Value MUST be int \n' +
                             'Get a ' + str(value))
        if key in self:
            if value == 0:
                self.pop(key)
                if self.isIsotope and len(key) > 3:
                    self.isIsotope = self._isIsotope()
            else:
                super().__setitem__(key, value)
        else:
            match = re.fullmatch(r"([A-Z][a-z]{0,2})(\[\d+\])?", key)
            if match is None:
                raise KeyError('have no element ' + str(key))
            e = match.group(1)
            if e not in mass.nist_mass:
                raise KeyError('have no element ' + str(e))
            m = match.group(2)
            if m is None:
                if value != 0:
                    super().__setitem__(key, value)
                return
            else:
                m = int(m[1:-1])
                if m not in mass.nist_mass[e]:
                    raise KeyError('element %s have no mass:%d' % (e, m))
                if m == int(round(mass.nist_mass[e][0][0])):
                    if value == 0:
                        self.pop(e)
                    else:
                        super().__setitem__(e, value)
                else:
                    if value != 0:
                        self.isIsotope = True
                        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        match = re.fullmatch(r"([A-Z][a-z]{0,2})(\[\d+\])?", key)
        if match is None:
            raise KeyError('have no element ' + str(key))
        e = match.group(1)
        if e not in mass.nist_mass:
            raise KeyError('have no element ' + str(e))
        m = match.group(2)
        if m is None:
            return 0
        else:
            m = int(m[1:-1])
            if m not in mass.nist_mass[e]:
                raise KeyError('element %s have no mass:%d' % (e, m))
            if m == int(round(mass.nist_mass[e][0][0])):
                return self[e]
            return 0

    def __str__(self):
        return self.toStr(False, True)

    def __repr__(self):
        return self.toStr(False, True)

    def __eq__(self, formula):
        if type(formula) != type(self) or len(self.data) != len(formula.data) or self.charge != formula.charge:
            return False
        for e, v in self.items():
            if v != formula[e]:
                return False
        return True

    def __hash__(self):
        x = 0
        for e, v in self.items():
            x ^= hash(e + str(v))
        x^=hash(self.charge)
        return x


if __name__ == "__main__":
    a = Formula({'C':2,'H':4,'H[2]':2,'O':1,'charge':-1,'C[13]':1})
    b = a.findOrigin()
    print(b,b.isIsotope)
