from typing import Tuple
from ._binary_search import indexNearest as _indexNearest_np, indexBetween as _indexBetween_np


def defaultMethod(array, index):
    return array[index]


def indexFirstNotSmallerThan(array, value, indexRange: Tuple[int, int] = None, method=defaultMethod):
    '''
    np.searchsorted(array,value,'left')
    or
    np.searchsorted(array,value)
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t + 1
        else:
            r = t
    return l


def indexFirstBiggerThan(array, value, indexRange: Tuple[int, int] = None, method=defaultMethod):
    '''
    np.searchsorted(array,value,'right')
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) <= value:
            l = t + 1
        else:
            r = t
    return l


def indexNearest(array, value, indexRange: Tuple[int, int] = None, method=defaultMethod) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = indexFirstBiggerThan(array, value, indexRange, method)

    if i == r or i > l and abs(method(array, i - 1) - value) < abs(method(array, i) - value):
        return i - 1
    else:
        return i


def indexNearest_np(array, value, indexRange=None):
    return _indexNearest_np(array, value, indexRange)


def indexBetween(array, valueRange, indexRange: Tuple[int, int] = None, method=defaultMethod) -> range:
    """
    get range from sorted array for value in (l,r)
    `indexRange`: (start,stop), contain array[start] to array[stop-1]
    make list = [index for index, item in enumerate(array) if l<item and item<r]
    """
    lvalue, rvalue = valueRange
    if indexRange is None:
        indexRange = (0, len(array))
    l = indexFirstNotSmallerThan(array, lvalue, indexRange, method)
    r = indexFirstBiggerThan(array, rvalue, indexRange, method)
    if l < r:
        return range(l, r)
    else:
        return range(l, l)


def indexBetween_np(array, valueRange, indexRange):
    return _indexBetween_np(array, valueRange, indexRange)


__all__ = [s for s in locals() if s.startswith('index')]
