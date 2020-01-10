# -*- coding: utf-8 -*-

import math
import scipy.optimize
from copy import copy
from typing import List, Tuple

import numpy as np

import OribitoolAbstract


def indexFindNearest(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)-1) if indexRange is None else indexRange
    while l + 1 < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t
        else:
            r = t
    if abs(method(array, l)-value) < abs(method(array, r)-value):
        return l
    else:
        return r


def valueFindNearest(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    '''
    `indexRange`: default=(0,len(array))
    '''
    return method(array, indexFindNearest(array, value, indexRange, method))


def indexBetween(array, valueRange, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    """
    get list from sorted array for value in (l,r)
    make list = [index for index, item in enumerate(array) if l<item and item<r]
    """
    lvalue, rvalue = valueRange
    l, r = (0, len(array)-1) if indexRange is None else indexRange
    ll = l
    t = r
    while ll < t:
        tt = (t + ll) >> 1
        if method(array, tt) < lvalue:
            ll = tt+1
        else:
            t = tt
    rr = r
    t = l
    while t < rr:
        tt = (t + rr) >> 1
        if method(array, tt) < rvalue:
            t = tt + 1
        else:
            rr = tt
    rr = t
    if ll < rr:
        return range(ll, rr)
    else:
        return range(0, 0)


def between(array, valueRange, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    """
    get list from sorted array for value in (l,r)
    make list = [item for item in array if l<item and item<r]
    """
    return [method(array, x) for x in indexBetween(array, valueRange, indexRange, method)]  # [ll:t-1]->[ll:t)


def findPeak(mz: np.ndarray, intensity: np.ndarray, begin: int, stop: int) -> (int, int):
    '''
    intensity[`stop`] must less than 1e-6, or `stop` == len(mz)
    find the first peak after begin
    return the peak with begin,xxx,xxx,xxx,end
    if don't find peak, return (`stop`,`stop`)
    '''
    if stop > len(mz):
        stop = len(mz)
    delta = 1e-6
    l = begin
    while l < stop and intensity[l] < delta:
        l += 1
    if l == stop:
        return (stop, stop)
    r = l
    l -= 1
    while r < stop and intensity[r] > delta:
        r += 1
    return (l, r)


class NormalDistributionFunc(OribitoolAbstract.fitPeakFunc):
    def __init__(self, params: List[tuple]):
        params = np.array(params)
        self.paramList = params
        peakPosition = params[:, 1]
        peakSigma = params[:, 2]
        peakSigmaNorm = peakSigma / \
            (np.sqrt(peakPosition / 200) * peakPosition)
        self.peakSigmaFit = np.median(peakSigmaNorm[peakSigmaNorm > 0])
        self.peakResFit = 1/(2*math.sqrt(2*math.log(2))*self.peakSigmaFit)

    @staticmethod
    def _func(mz: np.ndarray, a, mu, sigma):
        return a / (math.sqrt(2 * math.pi) * sigma) * np.exp(-0.5 * ((mz - mu) / sigma) ** 2)

    @staticmethod
    def getParam(peak: OribitoolAbstract.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param0 = (intensity.max() * mzmean / 56000, mzmean, mzmean / 140000)
        return scipy.optimize.curve_fit(NormalDistributionFunc._func, mz, intensity, param0)[0]

    @staticmethod
    def getNormalizedPeak(peak: OribitoolAbstract.Peak, param) -> OribitoolAbstract.Peak:
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        peakArea, peakPosition, peakSigma = param
        peakHeight = NormalDistributionFunc._func(peakPosition, *param)
        ret = copy(peak)
        ret.mz = (mz / peakPosition - 1) / math.sqrt(peakPosition / 200)
        ret.intensity = intensity / peakHeight
        return ret

    def normFunc(self, x):
        y = self._func(x, 1, 0, self.peakSigmaFit) / \
            self._func(0, 1, 0, self.peakSigmaFit)
        return y

    def _funcFit(self, mz: np.ndarray, a, mu):
        sigma = self.peakSigmaFit*math.sqrt(mu/200)*mu
        return NormalDistributionFunc._func(mz, a, mu, sigma)

    def getFittedParam(self, peak: OribitoolAbstract.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param = (intensity.max() * mzmean * self.peakSigmaFit * 2, mzmean)
        return scipy.optimize.curve_fit(self._funcFit, mz, intensity, param)[0]

    def getFittedPeak(self, peak: OribitoolAbstract.Peak, fittedParam=None):
        mz = peak.mz
        ret = copy(peak)
        ret.intensity = self._funcFit(
            mz, *(fittedParam if fittedParam is not None else self.getFittedParam(peak)))
        return ret


def linePeakCrossed(line: ((float, float), (float, float)), peak: OribitoolAbstract.Peak):
    p1, p2 = np.array(line)
    for index in range(len(peak.mz) - 1):
        tmp = np.stack([peak.mz[index:index + 2],
                        peak.intensity[index:index + 2]], axis=1)
        p3, p4 = tmp
        l = p2 - p1
        c1 = (np.cross(l, p3 - p1) > 0) ^ (np.cross(l, p4 - p1) > 0)
        l = p4 - p3
        c2 = (np.cross(l, p1 - p3) > 0) ^ (np.cross(l, p2 - p3) > 0)
        if c1 and c2:
            return True
    return False
