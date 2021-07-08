from typing import Tuple, TypeVar, List, Callable, Any
from ._binary_search import indexNearest as indexNearest_np, indexBetween as indexBetween_np


def defaultMethod(array, index):
    return array[index]


T = TypeVar("T")
K = TypeVar("K")


def indexFirstNotSmallerThan(array: List[T], value: K, indexRange: Tuple[int, int] = None, method: Callable[[List[T], int], K] = defaultMethod):
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


def indexFirstBiggerThan(array: List[T], value: K, indexRange: Tuple[int, int] = None, method: Callable[[List[T], int], K] = defaultMethod):
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


def indexNearest(array: List[T], value: K, indexRange: Tuple[int, int] = None, method: Callable[[List[T], int], K] = defaultMethod) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = indexFirstBiggerThan(array, value, indexRange, method)

    if i == r or i > l and abs(method(array, i - 1) - value) < abs(method(array, i) - value):
        return i - 1
    else:
        return i


def indexBetween(array: List[T], valueRange: Tuple[K, K], indexRange: Tuple[int, int] = None, method: Callable[[List[T], int], K] = defaultMethod) -> slice:
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
        return slice(l, r)
    else:
        return slice(l, l)


__all__ = [s for s in locals() if s.startswith('index')]
