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

import numpy as np
import scipy.optimize
import sklearn.linear_model
import sklearn.preprocessing
import statsmodels.nonparametric.smoothers_lowess as lowess

import OrbitoolBase
from OrbitoolUnpickler import Unpickler

from _OrbitoolFunc import indexNearest as indexNearest_np, indexBetween as indexBetween_np, getPeaks as _getPeaks, peakAt as peakAt_np, getNoise as _getNoise, denoiseWithLOD as _denoiseWithLOD, linePeakCrossed, NormalDistributionFunc as _NormalDistributionFunc, catTime, catTimeSeries as _catTimeSeries, interp1TimeSeriesAt as _interp1TimeSeriesAt

def nullSendStatus(fileTime: datetime.datetime, msg: str, index: int, length: int):
    pass


def defaultMethod(array, index):
    return array[index]

def indexFirstNotSmallerThan(array, value, indexRange: (int, int) = None, method=defaultMethod):
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

def indexFirstBiggerThan(array, value, indexRange: (int, int) = None, method=defaultMethod):
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

def indexNearest(array, value, indexRange: (int, int) = None, method=defaultMethod) -> int:
    '''
    `indexRange`: default=(0,len(array))
    '''
    l, r = (0, len(array)) if indexRange is None else indexRange
    i = indexFirstBiggerThan(array, value, indexRange, method)

    if i == r or i > 0 and abs(method(array, i-1)-value) < abs(method(array, i)-value):
        return i-1
    else:
        return i

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
    the first line of func.__doc__ will be shown message
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

def getPeaks(spectrum: OrbitoolBase.Spectrum, indexRange: (int, int) = None, mzRange: (float, float) = None) -> List[OrbitoolBase.Peak]:
    '''
    get peak divided by 0, result peak may have many peakPoint
    '''
    peaksRange = _getPeaks(
        spectrum.mz, spectrum.intensity, indexRange, mzRange)
    return [OrbitoolBase.Peak(spectrum, range(rstart, rstop)) for rstart, rstop in peaksRange]

def getNoise(spectrum: OrbitoolBase.Spectrum,  quantile=0.7, sendStatus=nullSendStatus) -> (np.ndarray, np.ndarray):
    """
    @quantile: sort peaks by intensity, select num*quantile-th biggest peak
    """
    fileTime = spectrum.fileTime
    msg = "calc noise"
    sendStatus(fileTime, msg, -1, 0)
    peakAt, noise, LOD = _getNoise(
        spectrum.mz, spectrum.intensity,  quantile)
    return peakAt, noise, LOD

def denoiseWithLOD(spectrum: OrbitoolBase.Spectrum, LOD: (float, float), peakAt: np.ndarray = None, minus=False, sendStatus=OrbitoolBase.nullSendStatus) -> OrbitoolBase.Spectrum:
    fileTime = spectrum.fileTime
    msg = "denoising"
    sendStatus(fileTime, msg, -1, 0)

    newSpectrum = copy(spectrum)
    if peakAt is None:
        peakAt = peakAt_np(intensity)
    mz, intensity = _denoiseWithLOD(
        spectrum.mz, spectrum.intensity, LOD, peakAt, minus)
    newSpectrum.mz = mz
    newSpectrum.intensity = intensity
    newSpectrum.peaks = getPeaks(newSpectrum)
    return newSpectrum


def denoise(spectrum: OrbitoolBase.Spectrum,  quantile=0.7, minus=False, sendStatus=OrbitoolBase.nullSendStatus):
    peakAt, noise, LOD = getNoise(spectrum,  quantile, sendStatus)
    return noise, LOD, denoiseWithLOD(spectrum, LOD, peakAt, minus, sendStatus)


class NormalDistributionFunc(_NormalDistributionFunc):
    def __init__(self, params: List[tuple]):
        params = np.array(params, dtype=np.float)
        self.paramList = params
        peakPosition = params[:, 1]
        peakSigma = params[:, 2]
        peakSigmaNorm = peakSigma / \
            (np.sqrt(peakPosition / 200) * peakPosition)
        self.peakSigmaFit = np.median(peakSigmaNorm[peakSigmaNorm > 0])
        self.peakResFit = 1/(2*math.sqrt(2*math.log(2))*self.peakSigmaFit)

    @staticmethod
    def getParam(peak: OrbitoolBase.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param0 = (intensity.max() * mzmean / 56000, mzmean, mzmean / 140000)
        return scipy.optimize.curve_fit(NormalDistributionFunc._func, mz, intensity, param0, maxfev=100)[0]

    @staticmethod
    def getNormalizedPeak(peak: OrbitoolBase.Peak, param) -> OrbitoolBase.Peak:
        '''
        return (mz, intensity)`
        '''
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        peakArea, peakPosition, peakSigma = param
        peakHeight = NormalDistributionFunc._func(peakPosition, *param)
        peak = OrbitoolBase.Peak(peak.spectrum, mz=(mz / peakPosition - 1) / math.sqrt(
            peakPosition / 200), intensity=intensity / peakHeight, originalPeak=peak)
        peak.addFittedParam(param)
        return peak

    def mergePeaks(self, peak1: OrbitoolBase.Peak, peak2: OrbitoolBase.Peak):
        newparam = NormalDistributionFunc.mergePeaksParam(
            peak1.fittedParam, peak2.fittedParam)
        if peak1.originalPeak is not None and peak1.originalPeak == peak2.originalPeak:
            newmz = peak1.originalPeak.mz
        else:
            newmz = np.unique(np.concatenate((peak1.mz, peak2.mz)))
            select = np.concatenate(
                ((newmz[1:] - newmz[:-1]) > 1e-9, np.ones(1, dtype=np.bool)))
            newmz = newmz[select]
        newIntensity = self._funcFit(newmz, *newparam)
        newPeak = OrbitoolBase.Peak(peak1.spectrum, mz=newmz, intensity=newIntensity, originalPeak=peak1.originalPeak, splitNum=(
            peak1.splitNum - 1) if isinstance(peak1.splitNum, int) else 1)
        peakIntensity = self._funcFit(newparam[1], *newparam)
        newPeak.addFittedParam(
            newparam, newparam[1], peakIntensity, newparam[0])
        return newPeak

    def normFunc(self, x):
        y = self._func(x, 1, 0, self.peakSigmaFit) / \
            self._func(0, 1, 0, self.peakSigmaFit)
        return y

    def _funcFit(self, mz: np.ndarray, a, mu):
        sigma = self.peakSigmaFit*np.sqrt(np.abs(mu)/200)*mu
        return NormalDistributionFunc._func(mz, a, mu, sigma)

    def getFittedParam(self, peak: OrbitoolBase.Peak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param = (intensity.max() * mzmean * self.peakSigmaFit * 2, mzmean)
        return scipy.optimize.curve_fit(self._funcFit, mz, intensity, param, maxfev=100)[0]

    def getIntensity(self, mz: np.ndarray, peak: OrbitoolBase.Peak):
        return self._funcFit(mz, *peak.fittedParam)

    def splitPeak(self, peak: OrbitoolBase.Peak, splitNum=None, force=False) -> List[OrbitoolBase.Peak]:
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
                    # select[:-1] = select[:-1] | select[1:]
                    # select[1:] = select[1:] | select[:-1]
                    select[:-1] |= select[1:]
                    select[1:] |= select[:-1]
                    newIntensity = newIntensity[select]
                    newIntensity[-1] = 0
                    newIntensity[0] = 0
                    newPeak = OrbitoolBase.Peak(
                        peak.spectrum, mz=mz[select], intensity=newIntensity, originalPeak=peak, splitNum=num)
                    newPeak.addFittedParam(
                        p, p[1], peakIntensity, p[0])
                    peaks.append(newPeak)
                    if len(peaks) > 1:
                        peaks.sort(key=lambda peak: peak.peakPosition)
                return peaks

            except RuntimeError:
                if force:
                    raise ValueError(
                        "can't fit use peaks num as "+str(splitNum))
            param = param[:-2]
        peakstr = [f'sigma={self.peakSigmaFit}']
        peakstr.append(','.join(['mz', 'intensity']))
        for row in np.stack((mz, intensity), 1):
            peakstr.append(','.join([str(r) for r in row]))
        peakstr = '\n'.join(peakstr)
        raise ValueError("can't fit peak in (%.5f,%.5f) at spectrum %s\nIf this peak is small, larger LOD may solve it\n%s" % (
            mz[0], mz[-1], peak.spectrum.timeRange[0].replace(microsecond=0).isoformat(), peakstr))

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


def file2Obj(path: str, sendStatus=None):
    try:
        with gzip.open(path, 'rb') as reader:
            return pickle.load(reader)
        if sendStatus is not None:
            sendStatus(datetime.datetime.now(),'old files',-1,0)
    except ModuleNotFoundError:
        with gzip.open(path, 'rb') as reader:
            return Unpickler(reader).load()


def recalcFormula(peaks: List[OrbitoolBase.Peak], ionCalc: OrbitoolBase.IonCalculatorHint, sendStatus=nullSendStatus):
    ppm = ionCalc.ppm
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
        formulaList = ionCalc.get(peak.peakPosition)

        def correct(formula: OrbitoolBase.FormulaHint):
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


def calculateResidual(fittedPeaks: OrbitoolBase.Peak, fitFunc: NormalDistributionFunc, fileTime: datetime.datetime = datetime.datetime.now(), sendStatus=nullSendStatus):
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

    sendStatus(fileTime, msg, length, length)
    msg = "concatenate residual"
    sendStatus(fileTime, msg, 0, 1)

    residualMz = np.concatenate(residualMz)
    residualInt = np.concatenate(residualInt)

    return (residualMz, residualInt)


def mergePeaks(peaks: List[OrbitoolBase.Peak], ppm: float, func: NormalDistributionFunc, ionCalc: OrbitoolBase.IonCalculatorHint, sameFormula=True):
    '''
    if `sameFormula` == True:
        will merge peaks which have same formula or both have no formula
    else:
        will average ignore formula
    '''
    newpeaks = []
    if len(peaks) > 0:
        newpeaks.append(peaks[0])
    for i in range(1, len(peaks)):
        peak1 = newpeaks[-1]
        peak2 = peaks[i]
        if np.abs(peak1.peakPosition / peak2.peakPosition - 1) < ppm:
            merge = False
            formulaList = None
            if sameFormula:
                if peak1.formulaList is None and peak2.formulaList is None:
                    merge = True
                    formulaList = []
                elif peak1.formulaList is not None and peak2.formulaList is not None:
                    if set(peak1.formulaList) == set(peak2.formulaList):
                        merge = True
                        formulaList = peak1.formulaList
            else:
                merge = True
                if peak1.handled and peak2.handled:
                    formulaList = list(set(peak1.formulaList) &
                                       set(peak2.formulaList))
                    formulaList.sort(key=lambda formula: formula.mass())
                elif peak1.handled:
                    formulaList = peak1.formulaList
                elif peak2.handled:
                    formulaList = peak2.formulaList
            if merge:
                newpeak = func.mergePeaks(peak1, peak2)
                if formulaList is None:
                    formulaList = ionCalc.get(newpeak.peakPosition)
                newpeak.addFormula(formulaList)
                newpeaks.pop()
                newpeaks.append(newpeak)
                continue
        newpeaks.append(peak2)
    return newpeaks

def catTimeSeries(timeSeries1: OrbitoolBase.TimeSeries, timeSeries2: OrbitoolBase.TimeSeries):
    time,ints=_catTimeSeries(timeSeries1.time,timeSeries1.intensity,timeSeries2.time,timeSeries2.intensity)
    return OrbitoolBase.TimeSeries(time,ints,timeSeries1.mz,timeSeries1.ppm,timeSeries1.tag)

def interp1TimeSeries(timeSeries: OrbitoolBase.TimeSeries, totalTime: np.ndarray) -> OrbitoolBase.TimeSeries:
    '''
    interpolate
    '''
    interAt = _interp1TimeSeriesAt(timeSeries.time, totalTime)
    if len(interAt) == 0:
        return timeSeries
    func = scipy.interpolate.interp1d(timeSeries.time.astype(float), timeSeries.intensity, 'linear')
    ints = func(interAt.astype(float))
    time = np.concatenate((timeSeries.time, interAt))
    ints=np.concatenate((timeSeries.intensity,ints))
    index = time.argsort()
    return OrbitoolBase.TimeSeries(time[index],ints[index],timeSeries.mz,timeSeries.ppm,timeSeries.tag)    

def getIsoTimeWithZone(dt: datetime.datetime):
    return dt.astimezone().isoformat()

def fromIsoTimeWithZone(s: str)->datetime.datetime:
    # return datetime.datetime.fromisoformat(s).replace(tzinfo=None) # py 3.7
    return datetime.datetime.strptime(s.split('+')[0], r"%Y-%m-%dT%H:%M:%S")

igorTimeStandard = datetime.datetime(1904, 1, 1)

def getIgorTime(dt: datetime.datetime):
    return int((dt - igorTimeStandard).total_seconds())

def fromIgorTime(t: int):
    return igorTimeStandard+datetime.timedelta(seconds=t)

matlabTimeStandard = np.float64(-719529).astype('M8[D]')

def getMatlabTime(dt: datetime.datetime):
    return (np.datetime64(dt) - matlabTimeStandard).astype('m8[s]').astype(float) / 86400.

def fromMatlabTime(t: float):
    return (matlabTimeStandard+np.float_(t*86400).astype('m8[s]')).astype(datetime.datetime)

excelTimeStandard = datetime.datetime(1899, 12, 31)

def getExcelTime(dt: datetime.datetime):
    return (dt - excelTimeStandard).total_seconds() / 86400.

def fromExcelTime(t: float):
    return excelTimeStandard+datetime.timedelta(seconds=t*86400)

def getTimesExactToS(dt: datetime.datetime):
    dt = dt.replace(microsecond=0)
    return [getIsoTimeWithZone(dt), getIgorTime(dt), getMatlabTime(dt), getExcelTime(dt)]

