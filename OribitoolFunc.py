# -*- coding: utf-8 -*-

import math
import os
from copy import copy
from typing import List, Tuple
import multiprocessing

import numpy as np
import scipy.optimize
import sklearn.preprocessing
import sklearn.linear_model

import OribitoolAbstract


def nullSendStatus(file, msg: str, index: int, length: int):
    '''
    `file`:type is `File`
    '''
    pass


def indexFindNearest(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    ll, rr = (0, len(array)) if indexRange is None else indexRange
    l = ll
    r = rr
    while l + 1 < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t
        else:
            r = t
    if r == rr or abs(method(array, l)-value) < abs(method(array, r)-value):
        return l
    else:
        return r


def valueFindNearest(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    '''
    `indexRange`: default=(0,len(array))
    '''
    return method(array, indexFindNearest(array, value, indexRange, method))


def indexBetween(array, valueRange, indexRange: (int, int) = None, method=(lambda array, index: array[index])) -> range:
    """
    get list from sorted array for value in (l,r)
    `indexRange`: (start,stop), contain array[start] to array[stop-1]
    make list = [index for index, item in enumerate(array) if l<item and item<r]
    """
    lvalue, rvalue = valueRange
    l, r = (0, len(array)) if indexRange is None else indexRange
    ll = l
    t = r
    while ll < t:
        tt = (t + ll) >> 1
        if method(array, tt) < lvalue:
            ll = tt+1
        else:
            t = tt
    rr = r
    t = ll
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
        return range(ll, ll)


def valueBetween(array, valueRange, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    """
    get list from sorted array for value in (l,r)
    make list = [item for item in array if l<item and item<r]
    """
    return [method(array, x) for x in indexBetween(array, valueRange, indexRange, method)]  # [ll:t-1]->[ll:t)


def findPeak(mz: np.ndarray, intensity: np.ndarray, begin: int, stop: int) -> (int, int):
    '''
    intensity[`stop`] must less than 1e-6, or `stop` == len(mz)
    find the first peak after begin
    if mz[begin] > 0, will find the first peak after first mz[i]=0, while i > begin
    seem to the end
    return the peak with begin,xxx,xxx,xxx,end
    if don't find peak, return (`stop`,`stop`)
    '''
    if stop > len(mz):
        stop = len(mz)
    delta = 1e-6
    l = begin
    while l < stop and intensity[l] > delta:
        l += 1
    while l < stop and intensity[l] < delta:
        l += 1
    if l == stop:
        return (stop, stop)
    r = l
    l -= 1
    while r < stop and intensity[r] > delta:
        r += 1
    if intensity[r] > delta:
        return (stop, stop)
    return (l, r)


def multiProcess(func, argsList: List[Tuple], filepath, cpu=None, sendStatusFunc=nullSendStatus):
    '''
    multi process
    the first line of func.__doc__ will be showed message
    '''
    if type(filepath) is list:
        if len(argsList) != len(filepath):
            raise ValueError('len(filepath)!=len(argsList)')
    if cpu is None or cpu > multiprocessing.cpu_count():
        cpu = multiprocessing.cpu_count()
    msg = ''
    for line in func.__doc__.splitlines():
        strip = line.strip()
        if len(strip) > 0:
            msg = strip
    length = len(argsList)
    if cpu == 1:
        results = []
        if type(filepath) is list:
            for i, args in enumerate(argsList):
                sendStatusFunc(filepath[i], msg, i, length)
                results.append(func(filepath[i], *args))
            sendStatusFunc(filepath[-1], msg, length, length)
        else:
            for i, args in enumerate(argsList):
                sendStatusFunc(filepath, msg, i, length)
                results.append(func(*args))
            sendStatusFunc(filepath, msg, length, length)
        return results
    else:
        with multiprocessing.Manager() as manager:
            queue = manager.Queue()
            with multiprocessing.Pool(cpu) as pool:
                if type(filepath) is list:
                    def process(func, filepath, args, signalQueue):
                        result = func(filepath, *args)
                        signalQueue.put(filepath)
                        return result
                    results: multiprocessing.pool.MapResult = pool.starmap_async(
                        process, [(func, path, args, queue) for path, args in zip(filepath, argsList)])
                    pool.close()
                    sendStatusFunc(filepath[0], msg, 0, length)
                    for i in range(length):
                        path = queue.get()
                        sendStatusFunc(path, msg, i, length)
                    return results.get()
                else:
                    def process(func, args, signalQueue):
                        result = func(*args)
                        signalQueue.put(True)
                        return result
                    results: multiprocessing.pool.MapResult = pool.starmap_async(
                        process, [(func, args, queue) for args in argsList])
                    pool.close()
                    for i in range(length):
                        sendStatusFunc(filepath, msg, i, length)
                        queue.get()
                    sendStatusFunc(filepath, msg, length, length)
                    return results.get()


class NormalDistributionFunc(OribitoolAbstract.FitPeakFunc):
    maxFitNum={1:100,2:200,3:1000,4:4000,5:6000,6:10000}

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
        return scipy.optimize.curve_fit(NormalDistributionFunc._func, mz, intensity, param0,maxfev=100)[0]

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
        return scipy.optimize.curve_fit(self._funcFit, mz, intensity, param, maxfev=100)[0]

    def getPeakPosition(self, fittedPeak: OribitoolAbstract.FittedPeak):
        return fittedPeak.fittedParam[1]

    def getPeakIntensity(self, fittedPeak: OribitoolAbstract.FittedPeak):
        return self._funcFit(fittedPeak.fittedParam[1], *fittedPeak.fittedParam)

    def getArea(self, fittedPeak: OribitoolAbstract.FittedPeak):
        return fittedPeak.fittedParam[0]

    def splitPeakAsParams(self, peak: OribitoolAbstract.Peak, splitNum=None) -> List[tuple]:
        super().splitPeakAsParams(peak, splitNum)
        peakAt = peak.peakAt()

        peaksNum=peak.peaksNum() if splitNum is None else splitNum

        u: np.ndarray = peak.mz[1:-1][peakAt]
        uu = [u[-1] + i + 1 for i in range(peaksNum - len(u))]
        u = np.concatenate((u, uu))

        param = []
        for i in range(peaksNum):
            param.append(i)
            param.append(u[i])

        for num in range(peaksNum,0,-1):
            try:
                def funcFit(mz: np.ndarray, *args):
                    return sum([self._funcFit(mz, args[2 * i], args[2 * i + 1]) for i in range(num)])
                param = scipy.optimize.curve_fit(
                    funcFit, peak.mz, peak.intensity, p0=param,maxfev=self.maxFitNum[num])[0]
                params = [(param[2*i],param[2*i+1]) for i in range(num)]
                return params
            except:
                if splitNum is not None:
                    raise ValueError("can't fit use peaks num as "+str(splitNum))
            param.pop()
            param.pop()
        raise ValueError("can't fit use peaks num")


def linePeakCrossed(line: ((float, float), (float, float)), peak: OribitoolAbstract.Peak):
    p1, p2 = np.array(line)
    if p1[0] > p2[0]:
        t = p1
        p1 = p2
        p2 = t
    mz = peak.mz
    intensity = peak.intensity
    r: range = indexBetween(mz, (p1[0], p2[0]))
    start = (r.start - 1) if r.start > 0 else 0
    stop = r.stop if r.stop < len(mz) else len(mz) - 1
    for index in range(start, stop):
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


class PolynomialRegressionFunc(OribitoolAbstract.MassCalibrationFunc):
    def __init__(self, mz: np.ndarray, ppm: np.ndarray, degree):
        featurizer = sklearn.preprocessing.PolynomialFeatures(degree=degree)
        regressor = sklearn.linear_model.LinearRegression()

        X = featurizer.fit_transform(mz.reshape(-1, 1))
        regressor.fit(X, ppm)

        self.featurizer = featurizer
        self.regressor = regressor

    def predictPpm(self, mz: np.ndarray):
        X = self.featurizer.transform(mz.reshape(-1, 1))
        return self.regressor.predict(X)

    def predictMz(self, mz: np.ndarray):
        X = self.featurizer.transform(mz.reshape(-1, 1))
        return mz*(1-self.regressor.predict(X))

    def __str__(self):
        pass
