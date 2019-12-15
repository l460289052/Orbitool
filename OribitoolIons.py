# -*- utf-8 -*-

import math
import re
from pyteomics import mass
from collections import UserDict


_print_order = ['C', 'H', 'O', 'N']
_print_order_set = set(_print_order)


class Ion(UserDict):
    '''
    '''

    def __init__(self, ion: str = None, **kwargs):
        '''
        Ion('CC[13]H5O-')
        Ion({'C':1,'C[13]':1,'H':5,'O':1},charge=-1)
        Ion({'C':1,'C[13]':1,'H':5,'O':1,'charge'=-1})
        Ion(C=1,H=2,O=1,charge=-1)
        '''
        super().__init__()
        self.charge = 0
        self.isIsotope = False
        try:
            if type(ion) is str:
                if not re.fullmatch(r"([A-Z][a-z]{0,2}(\[\d+\])?\d*)+[-+]", ion):
                    raise ValueError()
                charge = ion[-1]
                if charge == '+':
                    self.charge = 1
                elif charge == '-':
                    self.charge = -1
                for match in re.finditer(r"([A-Z][a-z]{0,2})(\[\d+\])?(\d*)", ion):
                    e = match.group(1)
                    m = match.group(2)  # if dismatch, None
                    num = match.group(3)
                    self.addElement(e, m[1:-1] if m else None, num)
                return

            dic=kwargs.copy()
            if type(ion) is dict:
                for k, v in ion.items():
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
            if len(dic)>0 and self.charge == 0:
                raise ValueError('wrong kwargs, charge must be provided')
        except ValueError as e:
            raise ValueError('wrong ion:' + str(e))

    def mass(self) -> float:
        return mass.calculate_mass(composition=self.data) - 0.0005486 * self.charge

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

    def Hmin(self) -> int:
        if self.isIsotope:
            return self.findOrigin().Hmin()
        Hmin = None
        if self['C'] == 0:
            Hmin = 0
        elif self['C'] <= 2:
            Hmin = 4 - self['N'] - 1
        elif self['C'] <= 6:
            Hmin = 6 - self['N'] - 1
        elif self['C'] <= 10:
            Hmin = 8 - self['N'] - 1
        elif self['C'] <= 16:
            Hmin = 10 - self['N'] - 1
        elif self['C'] <= 24:
            Hmin = 12 - self['N'] - 1
        elif self['C'] <= 32:
            Hmin = 14 - self['N'] - 1
        elif self['C'] <= 42:
            Hmin = 16 - self['N'] - 1
        elif self['C'] <= 54:
            Hmin = 18 - self['N'] - 1
        else:
            Hmin = int(math.ceil(0.3 * self['C'] - self['N'] - 1))
        return max(Hmin, 0)

    def Hmax(self) -> int:
        if self.isIsotope:
            return self.findOrigin().Hmax()
        return 2 * self['C'] + 2 + self['N']

    def Hpossible(self, NitrogenRule) -> bool:
        '''
        return Boolean indicating whether Hnum is possible
        '''
        if self.isIsotope:
            return self.findOrigin().Hpossible(NitrogenRule)

        if self['H'] > self.Hmax():
            return False

        return self['H'] >= self.Hmin() and (not NitrogenRule or (self['H'] + self['N']) % 2 == 1)

    def DBE(self) -> float:
        """
        only count C N H
        """
        if self.isIsotope:
            return self.findOrigin().DBE()
        return 1.0 + self['C'] + 0.5 * (self['N'] - self['H'] - self.charge)

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
                formula.data[origin] += self[e]
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

    def toStr(self, showAllProton: bool = False, withCharge: bool = True) -> str:
        s = []
        elements = list(self.keys())
        for e in _print_order:
            v = self[e]
            if v > 0:
                tmp = e
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
                tmp = e
                if v > 1:
                    tmp += str(v)
                s.append(tmp)

        if withCharge:
            return ''.join(s) + ('+' if self.charge == 1 else '-')
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

    def __eq__(self, ion):
        if type(ion) != type(self) or len(self.data) != len(ion.data) or self.charge != ion.charge:
            return False
        for e, v in self.items():
            if v != ion[e]:
                return False
        return True

    def __hash__(self):
        x = 0
        for e, v in self.items():
            x ^= hash(e + str(v))
        x^=hash(self.charge)
        return x


if __name__ == "__main__":
    a = Ion({'C':2,'H':4,'H[2]':2,'O':1,'charge':-1,'C[13]':1})
    b = a.findOrigin()
    print(b,b.isIsotope)
