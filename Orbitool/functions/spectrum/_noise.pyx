# distutils: language = c++
# cython: language_level = 3

from libc cimport math
from libcpp cimport bool
import cython
from cython.operator cimport preincrement as preinc, predecrement as predec

import numpy as np
cimport numpy as np
from numpy.polynomial import polynomial
import scipy

from ._spectrum cimport (getPeaksPositions, getNotZeroPositions,
    DoubleArray, DoubleArray2D, DoubleArray3D, DoubleOrArray, npdouble)
    
    
cpdef DoubleOrArray normFunc(DoubleOrArray x, double a, double mu, double sigma):
    return a/(math.sqrt(2*math.pi)*sigma)*np.exp(-0.5*np.power((x-mu)/sigma,2))

# noise

cdef np.ndarray[bool, ndim=1] getGlobalMask(DoubleArray mass):
    cdef double l = 0.5, r = 0.8
    cdef DoubleArray mass_defect = mass - np.floor(mass)
    # return (mass_defect>l) & (mass_defect<r)
    return np.abs(mass_defect - (l+r)/2) < (r-l)/2

cdef np.ndarray[bool, ndim=1] getMassPointMask(DoubleArray mass, double mass_point,
        double delta):
    return np.abs(mass - mass_point) < delta

cdef tuple getMassPointParams(DoubleArray mass, DoubleArray intensity,
        DoubleArray poly_coef, double global_std, double mass_point, double delta):
    if len(mass) <= 10:
        return False, None
    cdef np.ndarray[double, ndim=2] params = np.empty((2, 3), dtype = npdouble)
    cdef DoubleArray mass_bin, std_bin
    cdef np.ndarray[bool, ndim=1] mask

    mass_bin = np.arange(-5,5,1,dtype=npdouble) + (np.round(mass_point)+0.65)
    std_bin = np.empty_like(mass_bin)

    cdef double m
    cdef int i
    for i, m in enumerate(mass_bin):
        mask = np.abs(mass - m)<0.15
        std_bin[i] = -1 if mask.sum() == 0 else intensity[mask].std()
    mask = std_bin>0
    mass_bin = mass_bin[mask]
    std_bin = std_bin[mask]
    
    cdef tuple p0 = (100.0, mass_point, 1.0), \
        bounds = ([0, mass_point-0.1, 0], [np.inf, mass_point+0.1, np.inf])
    try:
        params[0] = scipy.curve_fit(normFunc, mass, intensity, p0=p0, bounds=bounds)[0]
    except RuntimeError:
        return False, None
    
    cdef bool flag = True
    if len(mass_bin)>3:
        try:
            params[1] = scipy.curve_fit(normFunc, mass_bin, std_bin, p0=p0, bounds=bounds)[0]
        except RuntimeError:
            flag = False
    else:
        flag = False
    
    cdef double global_peak_noise
    if not flag:
        global_peak_noise = noiseFuncAt(params[0, 1], poly_coef,
            np.empty((0, 3), dtype= npdouble))
        params[1] = params[0]
        params[1, 0] *= global_std / global_peak_noise
    return True, params

cdef double noiseFuncAt(double mass, DoubleArray poly_coef, DoubleArray2D norm_params):
    cdef noise = np.empty(1+norm_params.shape[0], dtype = npdouble)
    cdef DoubleArray norm_param
    noise[0] = polynomial.polyval(mass, poly_coef)
    for i, norm_param in enumerate(norm_params, 1):
        noise[i] = normFunc(mass, norm_param[0], norm_param[1], norm_param[2])
    return noise[i].max()


cdef DoubleArray noiseFunc(DoubleArray mass, DoubleArray poly_coef, DoubleArray2D norm_params):
    cdef list noise = np.empty((1+norm_params.shape[0], mass.size), dtype = npdouble)
    cdef DoubleArray norm_param
    noise[0] = polynomial.polyval(mass, poly_coef)
    for i, norm_param in enumerate(norm_params, 1):
        noise[i] = normFunc(mass, norm_param[0], norm_param[1], norm_param[2])
    return noise.max(axis=0)
    

def getNoiseParams(DoubleArray mass, DoubleArray intensity, double quantile,
        bool mass_dependent, double[:] mass_points, double mass_point_delta):
    cdef np.ndarray[bool, ndim=1] is_peak, global_mask, other_mask, quantile_mask
    is_peak = getPeaksPositions(intensity)
    mass = mass[1:-1][is_peak]
    intensity = intensity[1:-1][is_peak]

    global_mask = getGlobalMask(mass)
    cdef np.ndarray[bool, ndim=2] mass_masks = np.empty((mass_points.size, intensity.size), np.bool)
    cdef DoubleArray masked_mass, masked_intensity, poly_coef
    cdef double mass_point, std
    other_mask = global_mask.copy()
    # generate mask
    cdef int i
    for i, mass_point in enumerate(mass_points):
        mass_masks[i] = getMassPointMask(mass, mass_point, mass_point_delta)
        other_mask &= ~mass_masks[i]

    masked_intensity = intensity[other_mask]
    
    quantile_mask = masked_intensity < np.quantile(masked_intensity, quantile)
    masked_mass = mass[other_mask][quantile_mask]
    masked_intensity = masked_intensity[quantile_mask]
    # poly
    poly_coef = polynomial.polyfit(mass[other_mask][quantile_mask],
        masked_intensity, 1 if mass_dependent else 0)
    
    # norm
    std = masked_intensity.std()
    cdef list ret = []
    for i, mass_point in enumerate(mass_points):
        masked_mass = mass[mass_masks[i]]
        masked_intensity = intensity[mass_masks[i]]
        ret.append(getMassPointParams(masked_mass, masked_intensity, poly_coef,
            std, mass_point, mass_point_delta))
    return poly_coef, ret

cpdef tuple noiseLODFunc(DoubleArray mass, DoubleArray poly_coef,
        DoubleArray3D norm_params, double n_sigma):
    cdef DoubleArray noise, LOD
    noise = noiseFunc(mass, poly_coef, norm_params[:, 0])
    LOD = noise + n_sigma*noiseFunc(mass, poly_coef[:1], norm_params[:, 1])
    return noise, LOD

def getNoisePeaks(DoubleArray mass, DoubleArray intensity, DoubleArray poly_coef,
        DoubleArray3D norm_params, double n_sigma):
    cdef np.ndarray[bool, ndim=1] is_peak = getPeaksPositions(intensity), mask
    mass = mass[1:-1][is_peak]
    intensity = intensity[1:-1][is_peak]

    _, LOD = noiseLODFunc(mass, poly_coef, norm_params, n_sigma)

    mask = intensity<LOD
    return mass[mask], intensity[mask]

def denoiseWithParams(DoubleArray mass, DoubleArray intensity, DoubleArray poly_coef,
        DoubleArray3D norm_params, double n_sigma, bool subtract):
    cdef DoubleArray new_intensity, peak_mass, peak_intensity, noise, LOD
    cdef np.ndarray[bool, ndim=1] is_peak = getPeaksPositions(intensity)
    cdef np.ndarray[np.int32_t, ndim=1] ind_peak
    cdef int length = mass.size

    ind_peak = np.arange(0, length, dtype=np.int32)[1:-1][is_peak]
    peak_mass = mass[1:-1][is_peak]
    peak_intensity = intensity[1:-1][is_peak]

    noise, LOD = noiseLODFunc(mass, poly_coef, norm_params, n_sigma)

    ind_peak = ind_peak[peak_intensity > LOD[1:-1][is_peak]]

    new_intensity = np.zeros_like(intensity)
    cdef int l, r, ind
    cdef double ind_intensity
    with cython.boundscheck(False), cython.wraparound(False):
        for ind in ind_peak:
            l = ind-1
            r = ind+1
            while l>0 and intensity[l-1] < intensity[l]:
                predec(l)
            while r<length and intensity[r] > intensity[r+1]:
                preinc(r)
            if subtract:
                ind_intensity = intensity[ind]
                new_intensity[l:r+1] = intensity[l:r+1] * (1.-noise[ind]/ind_intensity)
            else:
                new_intensity[l:r+1] = intensity[l:r+1]
    
    cdef np.ndarray[bool, ndim=1] slt = getNotZeroPositions(new_intensity)
    return mass[slt], new_intensity[slt]
    