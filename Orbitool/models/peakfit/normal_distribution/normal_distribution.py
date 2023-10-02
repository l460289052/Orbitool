import math
from typing import List

import numpy as np
from scipy.optimize import curve_fit

from Orbitool.base import BaseRowStructure

from ....models.spectrum.spectrum import FittedPeak, Peak, PeakTags
from .nd import func, maxFitNum, mergePeaksParam
from ..base_fit_func import BaseFunc


def getParam(peak: Peak, resolution=140000):
    mz: np.ndarray = peak.mz
    intensity: np.ndarray = peak.intensity
    mu0 = mz.mean()
    # FWHM = 2sqrt(2ln2)*sigma for N(mu, sigma)
    sigma0 = mu0 / resolution / (2 * math.sqrt(2 * math.log(2)))
    a0 = intensity.max() * math.sqrt(2 * math.pi) * sigma0
    param0 = (a0, mu0, sigma0)
    return curve_fit(func, mz, intensity, param0, maxfev=100)[0]


def getNormalizedPeak(peak: Peak, param=None) -> FittedPeak:
    '''
    return (mz, intensity)`
    '''
    mz: np.ndarray = peak.mz
    intensity: np.ndarray = peak.intensity
    if param is None:
        param = getParam(peak)
    a, mu, sigma = param
    # peakHeight = NormalDistributionFunc._func(peakPosition, *param)
    peakHeight = a / (math.sqrt(2 * math.pi) * sigma)
    # move to 0 and change peak width
    mz_new = (mz / mu - 1) / math.sqrt(mu / 200)
    intensity_new = intensity / peakHeight
    peak = FittedPeak(mz_new, intensity_new, param, 0, 1, 1)
    return peak


class NormalDistributionFunc(BaseFunc, BaseRowStructure):
    peak_fit_sigma: float
    peak_fir_res: float

    @classmethod
    def FromParams(cls, params: List[tuple]):
        params = np.array(params, dtype=np.float64)
        peak_position = params[:, 1]
        peak_sigma = params[:, 2]
        peak_sigma_norm = peak_sigma / \
            (np.sqrt(peak_position / 200) * peak_position)
        peak_fit_sigma = np.median(peak_sigma_norm[peak_sigma_norm > 0])
        peak_fit_res = 1 / \
            (2 * math.sqrt(2 * math.log(2)) * peak_fit_sigma)
        return cls(peak_fit_sigma=peak_fit_sigma, peak_fit_res=peak_fit_res)

    @classmethod
    def FromNormPeaks(cls, peaks: List[FittedPeak]):
        return cls.FromParams([peak.fitted_param for peak in peaks])

    def mergePeaks(self, peak1: FittedPeak, peak2: FittedPeak) -> FittedPeak:
        param = mergePeaksParam(peak1.fitted_param, peak2.fitted_param)

        mz = np.unique(np.concatenate((peak1.mz, peak2.mz)))
        select = np.concatenate(
            ((mz[1:] - mz[:-1]) > 1e-9, np.ones(1, dtype=np.bool)))
        mz = mz[select]

        intensity = self._funcFit(mz, *param)
        peak_position = param[1]
        area = param[0]
        peak_intensity = self._funcFit(peak_position, *param)
        tags = set(peak1.tags)
        tags.update(peak2.tags)
        peak = FittedPeak(mz, intensity, param, peak_position, peak_intensity,
                          area, ''.join(tags))
        return peak

    def normFunc(self, x):
        y = func(x, 1, 0, self.peak_fit_sigma) / \
            func(0, 1, 0, self.peak_fit_sigma)
        return y

    def _funcFit(self, mz: np.ndarray, a, mu):
        sigma = self.peak_fit_sigma * math.sqrt(abs(mu) / 200) * mu
        return func(mz, a, mu, sigma)

    def func(self, mz: np.ndarray, params):
        return self._funcFit(mz, *params)

    def getFittedParam(self, peak: FittedPeak):
        mz: np.ndarray = peak.mz
        intensity: np.ndarray = peak.intensity
        mzmean = mz.mean()
        param = (intensity.max() * mzmean * self.peak_fit_sigma * 2, mzmean)
        return curve_fit(self._funcFit, mz, intensity, param, maxfev=100)[0]

    def getIntensity(self, mz: np.ndarray, peak: FittedPeak):
        return self._funcFit(mz, *peak.fitted_param)

    def splitPeak(self, peak: Peak, split_num=None, force=False) -> List[FittedPeak]:
        id_peak = peak.idPeak
        if split_num is None:
            split_num = len(id_peak)

        if split_num > 15:
            split_num = 15

        u = np.array([(pint / self._funcFit(pmz, 1, pmz), pmz)
                      for pmz, pint in zip(peak.mz[1:-1][id_peak],
                                           peak.intensity[1:-1][id_peak])])
        uu = [(u[-1, 0] + i + 1, 0) for i in range(split_num - u.shape[0])]
        if len(uu) > 0:
            uu = np.concatenate((u, uu), axis=0)
        else:
            uu = u

        index = uu[:, 0].argsort()
        uu = uu[index[::-1]]
        uu = uu[:split_num]
        param = uu.reshape(-1)

        mz = peak.mz
        intensity = peak.intensity
        mz_min = mz[0]  # mz.min()
        mz_max = mz[-1]  # mz.max()
        for num in range(split_num, 0, -1):
            try:
                def funcFit(mz: np.ndarray, *args):
                    return sum([self._funcFit(mz, args[2 * i], args[2 * i + 1]) for i in range(num)])
                fittedParam = curve_fit(
                    funcFit, mz, intensity, p0=param, maxfev=maxFitNum(num))[0]
                params = np.stack((fittedParam[::2], fittedParam[1::2]), 1)
                m = params[:, 1]
                if m.min() < mz_min or m.max() > mz_max or any(m[1:] - m[:-1] < 1e-6):
                    raise RuntimeError()

                return self.generate_peak_from_param(mz, params)

            except RuntimeError:
                if force:
                    raise ValueError(
                        "can't fit use peaks num as " + str(split_num))
            param = param[:-2]
        # peakstr = [f'sigma={self.peak_fit_sigma}']
        # peakstr.append(','.join(['mz', 'intensity']))
        # for row in np.stack((mz, intensity), 1):
        #     peakstr.append(','.join([str(r) for r in row]))
        # peakstr = '\n'.join(peakstr)
        # raise ValueError("can't fit peak in (%.5f,%.5f) \nIf this peak is small, larger LOD may solve it\n%s" % (
        #     mz[0], mz[-1], peakstr))
        index = u[:, 1].argsort()
        u = u[index[::-1]]
        u = u[:split_num]
        u = u
        return self.generate_peak_from_param(mz, u, PeakTags.Fail.value)

    def generate_peak_from_param(self, mz: np.ndarray, params: np.ndarray, tag=""):
        peaks: List[FittedPeak] = []
        for p in params:
            peak_intensity = self._funcFit(p[1], *p)
            if peak_intensity < 0:
                if tag == PeakTags.Fail.value:
                    continue
                raise RuntimeError()
            new_intensity = self._funcFit(mz, *p)
            select = new_intensity > 1e-6
            select[:-1] |= select[1:]
            select[1:] |= select[:-1]
            new_intensity = new_intensity[select]
            if len(new_intensity) == 0:
                if tag == PeakTags.Fail.value:
                    continue
                raise RuntimeError()
            new_intensity[-1] = 0
            new_intensity[0] = 0
            new_peak = FittedPeak(
                mz[select], new_intensity, p, p[1], peak_intensity, p[0], tag)
            peaks.append(new_peak)
        if len(peaks) > 1:
            peaks.sort(key=lambda peak: peak.peak_position)
        return peaks
