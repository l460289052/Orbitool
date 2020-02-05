# -*- coding: utf-8 -*-

import math
import os
import gzip
from copy import copy
from typing import List, Tuple, Iterable
import datetime
import traceback
import multiprocessing
import pickle

import numpy as np
from numba import jit, njit, numpy_extensions
import scipy.optimize
import sklearn.preprocessing
import sklearn.linear_model

import OribitoolAbstract
import OribitoolGuessIons


def nullSendStatus(fileTime: datetime.datetime, msg: str, index: int, length: int):
    pass

def defaultMethod(array, index):
    return array[index]

defaultMethod_njit=njit(defaultMethod)

def indexFirstNotSmallerThan(array, value, indexRange: (int, int) = None, method=defaultMethod):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t + 1
        else:
            r = t
    return l

@njit(cache=True)
def indexFirstNotSmallerThan_njit(array, value, indexRange: (int, int) = None, method=defaultMethod_njit):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t + 1
        else:
            r = t
    return l

def indexFirstBiggerThan(array, value, indexRange: (int, int) = None, method=defaultMethod):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) <= value:
            l = t + 1
        else:
            r = t
    return l

@njit(cache=True)
def indexFirstBiggerThan_njit(array, value, indexRange: (int, int) = None, method=defaultMethod_njit):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) <= value:
            l = t + 1
        else:
            r = t
    return l

def indexNearest(array, value, indexRange: (int, int) = None, method=defaultMethod) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = indexFirstBiggerThan(array, value, indexRange, method)

    if i == r or abs(method(array, i-1)-value) < abs(method(array, i)-value):
        return i-1
    else:
        return i

@njit(cache=True)
def indexNearest_njit(array, value, indexRange: (int, int) = None, method=defaultMethod_njit) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = indexFirstBiggerThan_njit(array, value, indexRange, method)

    if i == r or abs(method(array, i-1)-value) < abs(method(array, i)-value):
        return i-1
    else:
        return i

def valueNearest(array, value, indexRange: (int, int) = None, method=defaultMethod):
    '''
    `indexRange`: default=(0,len(array))
    '''
    return method(array, indexNearest(array, value, indexRange, method))

@njit(cache=True)
def valueNearest_njit(array, value, indexRange: (int, int) = None, method=defaultMethod_njit):
    '''
    `indexRange`: default=(0,len(array))
    '''
    return method(array, indexNearest_njit(array, value, indexRange, method))

def indexBetween(array, valueRange, indexRange: (int, int) = None, method=defaultMethod) -> range:
    """
    get list from sorted array for value in (l,r)
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

@njit(cache=True)
def indexBetween_njit(array, valueRange, indexRange: (int, int) = None, method=defaultMethod_njit) -> (int, int):
    lvalue, rvalue = valueRange
    if indexRange is None:
        indexRange = (0, len(array))
    l = indexFirstNotSmallerThan_njit(array, lvalue, indexRange, method)
    r = indexFirstBiggerThan_njit(array, rvalue, indexRange, method)
    if l < r:
        return (l, r)
    else:
        return (l, l)


def valueBetween(array, valueRange, indexRange: (int, int) = None, method=defaultMethod):
    """
    get list from sorted array for value in (l,r)
    make list = [item for item in array if l<item and item<r]
    """
    return [method(array, x) for x in indexBetween(array, valueRange, indexRange, method)]  # [ll:t-1]->[ll:t)


@njit(cache=True)
def findPeak(mz: np.ndarray, intensity: np.ndarray, indexRange: (int, int)) -> (int, int):
    '''
    intensity[`stop`] must less than 1e-6, or `stop` == len(mz)
    find the first peak after begin
    if mz[begin] > 0, will find the first peak after first mz[i]=0, while i > begin
    seem to the end
    return the peak with begin,xxx,xxx,xxx,end
    if don't find peak, return range(`stop`,`stop`)
    '''
    start, stop = indexRange
    if stop > len(mz):
        stop = len(mz)
    delta = 1e-6
    l = start
    while l < stop and intensity[l] > delta:
        l += 1
    while l < stop and intensity[l] < delta:
        l += 1
    if l == stop:
        return (stop,stop)
    r = l
    l -= 1
    while r < stop and intensity[r] > delta:
        r += 1
    if intensity[r] > delta:
        return (stop,stop)
    return (l, r + 1)


def processWithTime(func, fileTime, args, signalQueue):
    result = None
    try:
        result = func(fileTime, *args)
    except Exception as e:
        with open('error.txt', 'a') as file:
            print('', datetime.datetime.now, str(e), sep='\n', file=file)
            traceback.print_exc(file=file)
            print(str(e))
            traceback.print_exc()
    signalQueue.put(fileTime)
    return result


def processWithoutPath(func, args, signalQueue):
    result = None
    try:
        result = func(*args)
    except Exception as e:
        with open('error.txt', 'a') as file:
            print('', datetime.datetime.now, str(e), sep='\n', file=file)
            traceback.print_exc(file=file)
            print(str(e))
            traceback.print_exc()
    signalQueue.put(True)
    return result


def multiProcess(func, argsList: List[Tuple], fileTime, cpu=None, sendStatusFunc=nullSendStatus):
    '''
    multi process
    the first line of func.__doc__ will be showed message
    if fileTime is a list, func's first arguement must be fileTime
    '''
    if type(fileTime) is list:
        if len(argsList) != len(fileTime):
            raise ValueError('len(fileTime)!=len(argsList)')
    if cpu is None or cpu >= multiprocessing.cpu_count():
        cpu = multiprocessing.cpu_count() - 1
    if cpu <= 0:
        cpu = 1
    msg = ''
    if func.__doc__ is not None:
        for line in func.__doc__.splitlines():
            strip = line.strip()
            if len(strip) > 0:
                msg = strip
                break
    length = len(argsList)
    if cpu == 1:
        results = []
        if type(fileTime) is list:
            for i, args in enumerate(argsList):
                sendStatusFunc(fileTime[i], msg, i, length)
                results.append(func(fileTime[i], *args))
            sendStatusFunc(fileTime[-1], msg, length, length)
        else:
            for i, args in enumerate(argsList):
                sendStatusFunc(fileTime, msg, i, length)
                results.append(func(*args))
            sendStatusFunc(fileTime, msg, length, length)
        return results
    else:
        with multiprocessing.Manager() as manager:
            queue = manager.Queue()
            with multiprocessing.Pool(cpu) as pool:
                if type(fileTime) is list:
                    results: multiprocessing.pool.MapResult = pool.starmap_async(
                        processWithTime, [(func, time, args, queue) for time, args in zip(fileTime, argsList)])
                    pool.close()
                    sendStatusFunc(fileTime[0], msg, 0, length)
                    for i in range(length):
                        time = queue.get()
                        sendStatusFunc(time, msg, i, length)
                    return results.get()
                else:
                    results: multiprocessing.pool.MapResult = pool.starmap_async(
                        processWithTime, [(func, args, queue) for args in argsList])
                    pool.close()
                    for i in range(length):
                        sendStatusFunc(filetime, msg, i, length)
                        queue.get()
                    sendStatusFunc(filetime, msg, length, length)
                    return results.get()


class iterator(object):
    def __init__(self, l: Iterable):
        self._iter = iter(l)
        try:
            self._value = next(self._iter)
            self._end = False
        except StopIteration:
            self._value = None
            self._end = True
        self._index = 0

    @property
    def index(self):
        return self._index

    @property
    def value(self):
        return self._value if not self.end else None

    @property
    def end(self) -> bool:
        return self._end

    def next(self):
        if not self.end:
            try:
                self._value = next(self._iter)
            except StopIteration:
                self._end = True
            self._index += 1


class NormalDistributionFunc(OribitoolAbstract.FitPeakFunc):
    maxFitNum = {1: 100, 2: 200, 3: 1000, 4: 4000, 5: 6000, 6: 10000}

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
    @njit(cache=True)
    def _func(mz: np.ndarray, a, mu, sigma):
        return a / (np.sqrt(2 * np.pi) * sigma) * np.exp(-0.5 * ((mz - mu) / sigma) ** 2)

    @staticmethod
    def getParam(peak: OribitoolAbstract.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param0 = (intensity.max() * mzmean / 56000, mzmean, mzmean / 140000)
        return scipy.optimize.curve_fit(NormalDistributionFunc._func, mz, intensity, param0, maxfev=100)[0]

    @staticmethod
    def getNormalizedPeak(peak: OribitoolAbstract.Peak, param) -> Tuple[np.ndarray, np.ndarray]:
        '''
        return (mz, intensity)`
        '''
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        peakArea, peakPosition, peakSigma = param
        peakHeight = NormalDistributionFunc._func(peakPosition, *param)
        return ((mz / peakPosition - 1) / math.sqrt(peakPosition / 200), intensity / peakHeight)

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

    def splitPeakAsParams(self, peak: OribitoolAbstract.Peak, splitNum=None, force=False) -> List[tuple]:
        super().splitPeakAsParams(peak, splitNum)
        peakAt = peak.peakAt()

        if splitNum is None:
            splitNum = peak.peaksNum

        u: np.ndarray = np.stack(
            (peak.mz[1:-1][peakAt], peak.intensity[1:-1][peakAt]), axis=1)
        uu = [(u[-1, 0] + i + 1, 0) for i in range(splitNum - u.shape[0])]
        if len(uu) > 0:
            u = np.concatenate((u, uu), axis=0)

        index = np.argsort(u[:, 1])
        u = u[np.flip(index)]

        param = np.flip(u, axis=1).reshape(-1)

        mz = peak.mz
        intensity = peak.intensity
        mzMin = mz[0]  # mz.min()
        mzMax = mz[-1]  # mz.max()
        for num in range(splitNum, 0, -1):
            try:
                def funcFit(mz: np.ndarray, *args):
                    return sum([self._funcFit(mz, args[2 * i], args[2 * i + 1]) for i in range(num)])
                fittedParam = scipy.optimize.curve_fit(
                    funcFit, mz, intensity, p0=param, maxfev=self.maxFitNum[num])[0]
                params = [(fittedParam[2*i], fittedParam[2*i+1])
                          for i in range(num)]
                for p in params:
                    if p[1] < mzMin or p[1] > mzMax:
                        raise Exception()
                return params
            except:
                if force:
                    raise ValueError(
                        "can't fit use peaks num as "+str(splitNum))
            param = param[:-2]
        raise ValueError("can't fit peak  at (%.5f,%.5f)" % (mz[0], mz[-1]))

@njit(cache=True)
def linePeakCrossed(line: ((float, float), (float, float)), peak: Tuple[np.ndarray,np.ndarray]):
    line = np.array(line)
    p1 = line[0]
    p2 = line[1]
    if p1[0] > p2[0]:
        t = p1
        p1 = p2
        p2 = t
    mz = peak[0]
    intensity = peak[1]
    start, stop = indexBetween_njit(mz,(p1[0],p2[0]))
    start = (start - 1) if start > 0 else 0
    if stop >= len(mz):
        stop = len(mz) - 1
    for index in range(start, stop):
        tmp = np.stack((mz[index:index + 2],
                        intensity[index:index + 2]), axis=1)
        p3 = tmp[0]
        p4 = tmp[1]
        l = p2 - p1
        c1 = (numpy_extensions.cross2d(l, p3 - p1) > 0) ^ (numpy_extensions.cross2d(l, p4 - p1) > 0)
        l = p4 - p3
        c2 = (numpy_extensions.cross2d(l, p1 - p3) > 0) ^ (numpy_extensions.cross2d(l, p2 - p3) > 0)
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


def obj2File(path: str, obj):
    # with open(path, 'wb') as writer:
    with gzip.open(path, 'wb', compresslevel=2) as writer:
        pickle.dump(obj, writer)


def file2Obj(path: str):
    # with open(path, 'rb') as reader:
    with gzip.open(path, 'rb') as reader:
        return pickle.load(reader)


def standardPeakFittedPeakSimpleMatch(speaks: List[OribitoolAbstract.StandardPeak], fpeaks: List[OribitoolAbstract.FittedPeak], ppm, srange: range = None, frange: range = None) -> List[Tuple[OribitoolAbstract.FittedPeak, OribitoolAbstract.StandardPeak]]:
    if srange is not None:
        speaks = speaks[srange.start:srange.stop:srange.step]
    if frange is not None:
        fpeaks = fpeaks[frange.start:frange.stop:frange.step]
    lf = 0
    rf = len(speaks)
    ret=[]
    for speak in speaks:
        lf = indexNearest(fpeaks, speak.peakPosition, (lf, rf), (lambda fpeaks, index: fpeaks[index].peakPosition))
        if lf == rf:
            continue
        fpeak = fpeaks[lf]
        if abs(fpeak.peakPosition / speak.peakPosition - 1) < ppm:
            ret.append((fpeak,speak))
    return ret

        

def standardPeakFittedPeakHungaryMatch(speaks: List[OribitoolAbstract.StandardPeak], fpeaks: List[OribitoolAbstract.FittedPeak], ppm, srange: range = None, frange: range = None):
    pass

def recalcFormula(peaks: List[Tuple[OribitoolAbstract.FittedPeak, OribitoolAbstract.StandardPeak]], ionCalc: OribitoolGuessIons.IonCalculator):
    ppm = ionCalc.errppm
    minratio = 1 - ppm
    maxratio = 1 + ppm
    for fpeak, speak in peaks:
        if speak.handled:
            continue
        intensity = fpeak.peakIntensity
        formulaList = ionCalc.calc(speak.peakPosition)
        def correct(formula: OribitoolGuessIons.Formula):
            if not formula.isIsotope:
                return True
            ratio = formula.relativeAbundance() * 1.5
            origin = formula.findOrigin()
            mz = origin.mass()
            r: range = indexBetween(peaks, (mz * minratio, mz * maxratio), method=(lambda peaks, index: peaks[index][1].peakPosition))
            for i in r:
                fp, sp = peaks[i]
                for f in s.formulaList:
                    if origin == f and fp.peakIntensity * ratio > intensity:
                        return True
            return False
        speak.formulaList = [f for f in formulaList if correct(f)]