# -*- coding: utf-8 -*-

import csv
import datetime
import gzip
import math
import multiprocessing
import os
import pickle
import traceback
from collections.abc import Iterable
from copy import copy
from typing import List, Tuple

import numba
import numba.numpy_extensions
import numpy as np
import scipy.optimize
import sklearn.linear_model
import sklearn.preprocessing
import statsmodels.nonparametric.smoothers_lowess as lowess

import OribitoolBase
import OribitoolGuessIons


def nullSendStatus(fileTime: datetime.datetime, msg: str, index: int, length: int):
    pass


def defaultMethod(array, index):
    return array[index]


defaultMethod_njit = numba.njit(defaultMethod)


def indexFirstNotSmallerThan(array, value, indexRange: (int, int) = None, method=defaultMethod):
    l, r = (0, len(array)) if indexRange is None else indexRange
    while l < r:
        t = (l + r) >> 1
        if method(array, t) < value:
            l = t + 1
        else:
            r = t
    return l


@numba.njit(cache=True)
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


@numba.njit(cache=True)
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


@numba.njit(cache=True)
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


@numba.njit(cache=True)
def valueNearest_njit(array, value, indexRange: (int, int) = None, method=defaultMethod_njit):
    '''
    `indexRange`: default=(0,len(array))
    '''
    return method(array, indexNearest_njit(array, value, indexRange, method))


def indexBetween(array, valueRange, indexRange: (int, int) = None, method=defaultMethod) -> range:
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


@numba.njit(cache=True)
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


def processWithoutTime(func, args, signalQueue):
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
    if isinstance(fileTime, Iterable):
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
        if isinstance(fileTime, Iterable):
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
                if isinstance(fileTime, Iterable):
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
                        processWithoutTime, [(func, args, queue) for args in argsList])
                    pool.close()
                    for i in range(length):
                        sendStatusFunc(fileTime, msg, i, length)
                        queue.get()
                    sendStatusFunc(fileTime, msg, length, length)
                    return results.get()


@numba.njit(cache=True, parallel=True)
def _getPeaks_njit(mz: np.ndarray, intensity: np.ndarray, indexRange, mzRange) -> np.ndarray:
    start = 0
    stop = len(mz)
    if indexRange is not None:
        start, stop = indexRange
    elif mzRange is not None:
        start, stop = indexBetween_njit(mz, mzRange)
    mz = mz[start:stop]
    intensity = intensity[start:stop]
    index = np.arange(start, stop)

    delta = 1e-6
    peaksIndex = intensity > delta
    l = index[:-1][peaksIndex[1:] > peaksIndex[:-1]]
    r = index[1:][peaksIndex[:-1] > peaksIndex[1:]] + 1
    if l[0] + 1 >= r[0]:
        l = np.append((start,), l)
    if l[-1] + 1 >= r[-1]:
        r = np.append(r, np.array((stop,)))
    return np.stack((l, r), 1)


def getPeaks(spectrum: OribitoolBase.Spectrum, indexRange: (int, int) = None, mzRange: (float, float) = None) -> List[OribitoolBase.Peak]:
    '''
    get peak divided by 0, result peak may have many peakPoint
    '''
    peaksRange = _getPeaks_njit(
        spectrum.mz, spectrum.intensity, indexRange, mzRange)
    return [OribitoolBase.Peak(spectrum, range(rstart, rstop)) for rstart, rstop in peaksRange]


@numba.njit(cache=True)
def peakAt_njit(intensity: np.ndarray) -> np.ndarray:
    peakAt = intensity
    peakAt = peakAt[:-1] < peakAt[1:]
    peakAt = peakAt[:-1] > peakAt[1:]
    return peakAt

@numba.njit(cache=True, parallel=True)
def _getNoise_njit(mz, intensity,  quantile) -> np.ndarray:
    minMz = np.floor(mz[0])  # float
    maxMz = np.ceil(mz[1])  # float
    peakAt = peakAt_njit(intensity)
    mz = mz[1:-1][peakAt]
    intensity = intensity[1:-1][peakAt]

    l = 0.5
    r = 0.8
    tmp = mz - np.floor(mz)
    select = (tmp > l) & (tmp < r)
    noiseMz = mz[select]
    noiseInt = intensity[select]

    select = noiseInt < (noiseInt.mean() + noiseInt.std() * 3)
    noiseMz = noiseMz[select]
    noiseInt = noiseInt[select]
    noiseQuantile = np.quantile(noiseInt, quantile)
    noiseStd = np.std(noiseInt)

    return peakAt, (noiseMz, noiseInt), (noiseQuantile, noiseStd)


def getNoise(spectrum: OribitoolBase.Spectrum,  quantile=0.7, sendStatus=nullSendStatus) -> Tuple[np.ndarray, np.ndarray]:
    """
    @quantile: sort peaks by intensity, select num*quantile-th biggest peak
    """
    fileTime = spectrum.fileTime
    msg = "calc noise"
    sendStatus(fileTime, msg, -1, 0)
    peakAt, noise, LOD = _getNoise_njit(
        spectrum.mz, spectrum.intensity,  quantile)
    return peakAt, noise, LOD


@numba.njit(cache=True, parallel=True)
def _denoiseWithLOD_njit(mz: np.ndarray, intensity: np.ndarray, LOD: (float, float), peakAt: np.ndarray, minus=True) -> (np.ndarray, np.ndarray):
    length = len(mz)
    newIntensity = np.zeros_like(intensity)
    mean = LOD[0]
    std = LOD[1]
    MAX = mean + 3 * std

    # len = len(peak)
    peakmzIndex = np.arange(0, length)[1:-1][peakAt]
    # peakMz = mz[1:-1][peakAt]
    peakIntensity = intensity[1:-1][peakAt]

    arg = peakIntensity.argsort()
    peakmzIndex = peakmzIndex[arg]
    peakIntensity = peakIntensity[arg]

    thresholdIndex = indexFirstBiggerThan_njit(peakIntensity, MAX)
    peakmzIndex = peakmzIndex[thresholdIndex:]
    for i in numba.prange(len(peakmzIndex)):
        mzIndex = peakmzIndex[i]
        l = mzIndex - 1
        r = mzIndex + 1
        while l > 0 and intensity[l] > intensity[l - 1]:
            l -= 1
        while r < length and intensity[r] > intensity[r + 1]:
            r += 1
        if minus:
            peakI = intensity[mzIndex]
            newIntensity[l:r + 1] = intensity[l:r + 1] / peakI * (peakI - mean)
        else:
            newIntensity[l:r + 1] = intensity[l:r + 1]

    delta = 1e-6
    select = newIntensity > delta
    select[1:] = select[1:] | select[:-1]
    select[:-1] = select[:-1] | select[1:]
    mz = mz[select]
    newIntensity = newIntensity[select]
    return mz, newIntensity


def denoiseWithLOD(spectrum: OribitoolBase.Spectrum, LOD: (float, float), peakAt: np.ndarray = None, minus=False, sendStatus=OribitoolBase.nullSendStatus) -> OribitoolBase.Spectrum:
    fileTime = spectrum.fileTime
    msg = "denoising"
    sendStatus(fileTime, msg, -1, 0)

    newSpectrum = copy(spectrum)
    if peakAt is None:
        peakAt = peakAt_njit(intensity)
    mz, intensity = _denoiseWithLOD_njit(
        spectrum.mz, spectrum.intensity, LOD, peakAt, minus)
    newSpectrum.mz = mz
    newSpectrum.intensity = intensity
    newSpectrum.peaks = getPeaks(newSpectrum)
    return newSpectrum


def denoise(spectrum: OribitoolBase.Spectrum,  quantile=0.7, minus=False, sendStatus=OribitoolBase.nullSendStatus):
    peakAt, noise, LOD = getNoise(spectrum,  quantile, sendStatus)
    return noise, LOD, denoiseWithLOD(spectrum, LOD, peakAt, minus, sendStatus)


class NormalDistributionFunc:
    @staticmethod
    @numba.njit(cache=True)
    def maxFitNum(num):
        return int(np.arctan((num-5)/20)*20000+4050)

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
    @numba.njit(cache=True)
    def _func(mz: np.ndarray, a, mu, sigma):
        return a / (np.sqrt(2 * np.pi) * sigma) * np.exp(-0.5 * ((mz - mu) / sigma) ** 2)

    @staticmethod
    def getParam(peak: OribitoolBase.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param0 = (intensity.max() * mzmean / 56000, mzmean, mzmean / 140000)
        return scipy.optimize.curve_fit(NormalDistributionFunc._func, mz, intensity, param0, maxfev=100)[0]

    @staticmethod
    def getNormalizedPeak(peak: OribitoolBase.Peak, param) -> OribitoolBase.Peak:
        '''
        return (mz, intensity)`
        '''
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        peakArea, peakPosition, peakSigma = param
        peakHeight = NormalDistributionFunc._func(peakPosition, *param)
        peak = OribitoolBase.Peak(peak.spectrum, mz=(mz / peakPosition - 1) / math.sqrt(
            peakPosition / 200), intensity=intensity / peakHeight, originalPeak=peak)
        peak.addFittedParam(param)
        return peak

    def normFunc(self, x):
        y = self._func(x, 1, 0, self.peakSigmaFit) / \
            self._func(0, 1, 0, self.peakSigmaFit)
        return y

    def _funcFit(self, mz: np.ndarray, a, mu):
        sigma = self.peakSigmaFit*math.sqrt(mu/200)*mu
        return NormalDistributionFunc._func(mz, a, mu, sigma)

    def getFittedParam(self, peak: OribitoolBase.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param = (intensity.max() * mzmean * self.peakSigmaFit * 2, mzmean)
        return scipy.optimize.curve_fit(self._funcFit, mz, intensity, param, maxfev=100)[0]

    def getIntensity(self, mz: np.ndarray, peak: OribitoolBase.Peak):
        return self._funcFit(mz, *peak.fittedParam)

    def splitPeak(self, peak: OribitoolBase.Peak, splitNum=None, force=False) -> List[OribitoolBase.Peak]:
        peakAt = peak.peakAt()

        if splitNum is None:
            splitNum = peak.splitNum
        if splitNum > 20:
            splitNum = 20
        u: np.ndarray = np.stack(
            (peak.mz[1:-1][peakAt], peak.intensity[1:-1][peakAt]), axis=1)
        uu = [(u[-1, 0] + i + 1, 0) for i in range(splitNum - u.shape[0])]
        if len(uu) > 0:
            u = np.concatenate((u, uu), axis=0)

        index = np.argsort(u[:, 1])
        u = u[np.flip(index)]
        u = u[:splitNum]
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
                    funcFit, mz, intensity, p0=param, maxfev=self.maxFitNum(num))[0]
                params = np.stack((fittedParam[::2], fittedParam[1::2]), 1)
                m = params[:, 1]
                if m.min() < mzMin or m.max() > mzMax:
                    raise RuntimeError()

                peaks = []
                for p in params:
                    peakIntensity = self._funcFit(p[1], *p)
                    if peakIntensity < 0:
                        raise RuntimeError()
                    newIntensity = self._funcFit(mz, *p)
                    select = newIntensity > 1e-6
                    select[:-1] = select[:-1] | select[1:]
                    select[1:] = select[1:] | select[:-1]
                    newIntensity = newIntensity[select]
                    newIntensity[-1] = 0
                    newIntensity[0] = 0
                    newPeak = OribitoolBase.Peak(
                        peak.spectrum, mz=mz[select], intensity=newIntensity, originalPeak=peak, splitNum=num)
                    newPeak.addFittedParam(
                        p, p[1], peakIntensity, fittedParam[0])
                    peaks.append(newPeak)
                    if len(peaks) > 1:
                        peaks.sort(key=lambda peak: peak.peakPosition)
                return peaks

            except RuntimeError:
                if force:
                    raise ValueError(
                        "can't fit use peaks num as "+str(splitNum))
            param = param[:-2]
        with open('errorpeak.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['mz', 'intensity'])
            for row in np.stack((mz, intensity), 1):
                writer.writerow(row)
        raise ValueError("can't fit peak in (%.5f,%.5f) at spectrum %s" % (
            mz[0], mz[-1], peak.spectrum.timeRange[0].strftime(OribitoolBase.timeFormat)))


@numba.njit(cache=True)
def linePeakCrossed(line: ((float, float), (float, float)), mz: np.ndarray, intensity: np.ndarray):
    line = np.array(line)
    p1 = line[0]
    p2 = line[1]
    if p1[0] > p2[0]:
        t = p1
        p1 = p2
        p2 = t
    start, stop = indexBetween_njit(mz, (p1[0], p2[0]))
    start = (start - 1) if start > 0 else 0
    if stop >= len(mz):
        stop = len(mz) - 1
    for index in range(start, stop):
        tmp = np.stack((mz[index:index + 2],
                        intensity[index:index + 2]), axis=1)
        p3 = tmp[0]
        p4 = tmp[1]
        l = p2 - p1
        c1 = (numba.numpy_extensions.cross2d(l, p3 - p1) >
              0) ^ (numba.numpy_extensions.cross2d(l, p4 - p1) > 0)
        l = p4 - p3
        c2 = (numba.numpy_extensions.cross2d(l, p1 - p3) >
              0) ^ (numba.numpy_extensions.cross2d(l, p2 - p3) > 0)
        if c1 and c2:
            return True
    return False


class PolynomialRegressionFunc:
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


def recalcFormula(peaks: List[OribitoolBase.Peak], ionCalc: OribitoolGuessIons.IonCalculator, sendStatus=nullSendStatus):
    ppm = ionCalc.errppm
    minratio = 1 - ppm
    maxratio = 1 + ppm
    time = peaks[0].spectrum.fileTime if len(peaks) > 0 else None
    length = len(peaks)
    msg = "calc isotope"
    for index, peak in enumerate(peaks):
        if index % 100 == 0:
            sendStatus(time, msg, index, length)
        if peak.handled:
            continue
        intensity = peak.peakIntensity
        formulaList = ionCalc.calc(peak.peakPosition)

        def correct(formula: OribitoolGuessIons.Formula):
            if not formula.isIsotope:
                return True
            ratio = formula.relativeAbundance() * 1.5
            origin = formula.findOrigin()
            mz = origin.mass()
            r: range = indexBetween(peaks, (mz * minratio, mz * maxratio),
                                    method=(lambda peaks, index: peaks[index].peakPosition))
            for i in r:
                p = peaks[i]
                for f in p.formulaList:
                    if origin == f and p.peakIntensity * ratio > intensity:
                        return True
            return False
        peak.formulaList = [f for f in formulaList if correct(f)]

    sendStatus(time, msg, length, length)


def calculateResidual(fittedPeaks: OribitoolBase.Peak, fitFunc: NormalDistributionFunc, fileTime:datetime.datetime = datetime.datetime.now(), sendStatus=nullSendStatus):
    '''
    fittedPeaks will be changed
    '''
    residualMz = []
    residualInt = []
    msg = "calc residual"
    opeak = None
    omz = None
    ointensity = None
    length = len(fittedPeaks)
    for index, peak in enumerate(fittedPeaks):
        if index % 20 == 0:
            sendStatus(fileTime, msg, index, length)
        if opeak != peak.originalPeak:
            opeak = peak.originalPeak
            omz = opeak.mz
            ointensity = opeak.intensity
            ointensity = ointensity.copy()
            residualMz.append(omz)
            residualInt.append(ointensity)
        ointensity -= fitFunc._funcFit(
            omz, *peak.fittedParam)
        
    sendStatus(fileTime, msg, index, length)
    msg = "concatenate residual"
    sendStatus(fileTime, msg, 0,1)
   
    residualMz = np.concatenate(residualMz)
    residualInt = np.concatenate(residualInt)

    return (residualMz, residualInt)

