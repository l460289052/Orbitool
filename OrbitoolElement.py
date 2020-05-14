# -*- coding: utf-8 -*-
from typing import Dict, List

from _OrbitoolElement import setPara as _setPara, getPara as _getPara, getParas as _getParas


def setPara(e: str, v: list):
    '''
    v: min, max, DBE2, Hmin, Hmax, Omin, Omax
    '''
    v[0] = int(v[0])
    v[1] = int(v[1])
    return _setPara(e, v)


def getPara(e: str) -> list:
    return _getPara(e)


def getParas() -> Dict[str, list]:
    return _getParas()
