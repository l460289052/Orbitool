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
import scipy.optimize
import sklearn.preprocessing
import sklearn.linear_model

import OribitoolAbstract


def nullSendStatus(file, msg: str, index: int, length: int):
    '''
    `file`:type is `File`
    '''
    pass

def indexFindFirstNotSmallerThan(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t + 1
        else:
            r = t
    return l

def indexFindFirstBiggerThan(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) <= value:
            l = t + 1
        else:
            r = t
    return l
        
def valueFindFirstNotSmallerThan(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    return method(array, indexFindFirstNotSmallerThan(array, value, indexRange, method))

def valueFindFirstBiggerThan(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    return method(array, indexFindFirstBiggerThan(array, value, indexRange, method))


def indexFindNearest(array, value, indexRange: (int, int) = None, method=(lambda array, index: array[index])) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = indexFindFirstBiggerThan(array, value, indexRange, method)
    
    if i == r or abs(method(array, i-1)-value) < abs(method(array, i)-value):
        return i-1
    else:
        return i


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
    if indexRange is None:
        indexRange = (0, len(array))
    l = indexFindFirstNotSmallerThan(array, lvalue, indexRange, method)
    r = indexFindFirstBiggerThan(array, rvalue, indexRange, method)
    if l < r:
        return range(l, r)
    else:
        return range(l, l)


def valueBetween(array, valueRange, indexRange: (int, int) = None, method=(lambda array, index: array[index])):
    """
    get list from sorted array for value in (l,r)
    make list = [item for item in array if l<item and item<r]
    """
    return [method(array, x) for x in indexBetween(array, valueRange, indexRange, method)]  # [ll:t-1]->[ll:t)


def findPeak(mz: np.ndarray, intensity: np.ndarray, indexRange:range) -> range:
    '''
    intensity[`stop`] must less than 1e-6, or `stop` == len(mz)
    find the first peak after begin
    if mz[begin] > 0, will find the first peak after first mz[i]=0, while i > begin
    seem to the end
    return the peak with begin,xxx,xxx,xxx,end
    if don't find peak, return range(`stop`,`stop`)
    '''
    l = indexRange.start
    stop = indexRange.stop
    if stop > len(mz):
        stop = len(mz)
    delta = 1e-6
    while l < stop and intensity[l] > delta:
        l += 1
    while l < stop and intensity[l] < delta:
        l += 1
    if l == stop:
        return range(stop, stop)
    r = l
    l -= 1
    while r < stop and intensity[r] > delta:
        r += 1
    if intensity[r] > delta:
        return range(stop, stop)
    return range(l, r+1)


def processWithTime(func, fileTime, args, signalQueue):
    result=None
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
    result=None
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
    def __init__(self,l: Iterable):
        self._iter = iter(l)
        try:
            self._value = next(self._iter)
            self._end=False
        except StopIteration:
            self._value = None
            self._end=True
        self._index = 0

    @property
    def index(self):
        return self._index

    @property
    def value(self):
        return self._value if not self.end else None

    @property
    def end(self)->bool:
        return self._end

    def next(self):
        if not self.end:
            try:
                self._value = next(self._iter)
            except StopIteration:
                self._end=True
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
    def _func(mz: np.ndarray, a, mu, sigma):
        return a / (math.sqrt(2 * math.pi) * sigma) * np.exp(-0.5 * ((mz - mu) / sigma) ** 2)

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

    def splitPeakAsParams(self, peak: OribitoolAbstract.Peak, splitNum=None) -> List[tuple]:
        super().splitPeakAsParams(peak, splitNum)
        peakAt = peak.peakAt()

        peaksNum = peak.peaksNum if splitNum is None else splitNum

        u: np.ndarray = np.stack(
            (peak.mz[1:-1][peakAt], peak.intensity[1:-1][peakAt]), axis=1)
        uu = [(u[-1, 0] + i + 1, 0) for i in range(peaksNum - u.shape[0])]
        if len(uu) > 0:
            u = np.concatenate((u, uu), axis=0)

        index = np.argsort(u[:, 1])
        u = u[np.flip(index)]

        param = np.flip(u,axis=1).reshape(-1)

        mz = peak.mz
        intensity = peak.intensity
        mzMin = mz[0] # mz.min()
        mzMax = mz[-1]  # mz.max()
        for num in range(peaksNum, 0, -1):
            try:
                def funcFit(mz: np.ndarray, *args):
                    return sum([self._funcFit(mz, args[2 * i], args[2 * i + 1]) for i in range(num)])
                fittedParam = scipy.optimize.curve_fit(
                    funcFit, mz, intensity, p0=param, maxfev=self.maxFitNum[num])[0]
                params = [(fittedParam[2*i], fittedParam[2*i+1]) for i in range(num)]
                for p in params:
                    if p[1] < mzMin or p[1] > mzMax:
                        raise Exception()
                return params
            except:
                if splitNum is not None:
                    raise ValueError(
                        "can't fit use peaks num as "+str(splitNum))
            param=param[:-2]
        raise ValueError("can't fit peak  at (%.5f,%.5f)" % (mz[0],mz[-1]))


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



def obj2File(path: str, obj):
    # with open(path, 'wb') as writer:
    with gzip.open(path, 'wb', compresslevel=2) as writer:
        pickle.dump(obj,writer)


def file2Obj(path: str):
    # with open(path, 'rb') as reader:
    with gzip.open(path, 'rb') as reader:
        return pickle.load(reader)
