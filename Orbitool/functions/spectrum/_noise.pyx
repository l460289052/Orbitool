# distutils: language = c++
# cython: language_level = 3

from libc cimport math
from libcpp cimport bool as cbool
import cython
from cython.operator cimport preincrement as preinc, predecrement as predec

import numpy as np
cimport numpy as np
from numpy.polynomial import polynomial
from scipy.optimize import curve_fit

from ._spectrum cimport (getPeaksPositions, getNotZeroPositions,
    DoubleArray, DoubleArray2D, DoubleArray3D, DoubleOrArray)

npdouble = np.float64
    
cdef double bin_l = 0.5, bin_r = 0.8
cdef double bin_mid = (bin_l+bin_r)/2.0, bin_wid = (bin_r-bin_l)/2.0

    
cpdef DoubleArray normFunc(DoubleArray x, double a, double mu, double sigma):
    return a/(math.sqrt(2*math.pi)*sigma)*np.exp(-0.5*np.power((x-mu)/sigma,2))

cpdef double normFuncAt(double x, double a, double mu, double sigma):
    return a/(math.sqrt(2*math.pi)*sigma)*math.exp(-0.5*math.pow((x-mu)/sigma,2))

# noise

cdef np.ndarray[cbool, ndim=1] getGlobalMask(DoubleArray mass):
    cdef DoubleArray mass_defect = mass - np.floor(mass)
    # return (mass_defect>l) & (mass_defect<r)
    return np.abs(mass_defect - bin_mid) < bin_wid

cdef np.ndarray[cbool, ndim=1] getMassPointMask(DoubleArray mass, double mass_point,
        int delta):
    return np.abs(mass - math.round(mass_point) - bin_mid) < delta + bin_wid

cdef cbool getMassPointMasked(double mass, double mass_point, int delta):
    return math.fabs(mass - math.round(mass_point) - bin_mid) < delta+bin_wid

cdef tuple getMassPointParams(DoubleArray mass, DoubleArray intensity,
        DoubleArray poly_coef, double global_std, double mass_point, double delta):
    if len(mass) <= 10:
        return False, None
    cdef np.ndarray[double, ndim=2] params = np.empty((2, 3), dtype = npdouble)
    cdef DoubleArray mass_bin, std_bin
    cdef np.ndarray[cbool, ndim=1] mask

    mass_bin = np.arange(-delta,delta+1,1,dtype=npdouble) + (np.round(mass_point)+bin_mid)
    std_bin = np.empty_like(mass_bin)

    cdef double m
    cdef int i
    for i, m in enumerate(mass_bin):
        mask = np.abs(mass - m)<bin_wid
        std_bin[i] = -1 if mask.sum() == 0 else intensity[mask].std()
    mask = std_bin>0
    mass_bin = mass_bin[mask]
    std_bin = std_bin[mask]
    
    cdef tuple p0 = (100.0, mass_point, 1.0), \
        bounds = ([0, mass_point-0.1, 0], [np.inf, mass_point+0.1, np.inf])
    try:
        params[0] = curve_fit(normFunc, mass, intensity, p0=p0, bounds=bounds)[0]
    except RuntimeError:
        return False, None
    
    cdef cbool flag = True
    if len(mass_bin)>3:
        try:
            params[1] = curve_fit(normFunc, mass_bin, std_bin, p0=p0, bounds=bounds)[0]
        except RuntimeError:
            flag = False
    else:
        flag = False
    
    cdef double global_peak_noise
    if not flag:
        global_peak_noise = polynomial.polyval(params[0, 1], poly_coef)
        params[1] = params[0]
        if abs(global_peak_noise) < 1e-6:
            params[1, 0] = 0
        else:
            params[1, 0] *= global_std / global_peak_noise
    return True, params

def getGlobalShownNoise(DoubleArray poly_coef, double n_sigma, double std):
    cdef double noise, lod
    if poly_coef is None:
        noise = 0
    else:
        noise = polynomial.polyval(200, poly_coef)
    lod = noise + n_sigma * std
    return noise, lod

def updateGlobalParam(DoubleArray poly_coef, double n_sigma, double noise, double lod):
    if len(poly_coef) == 2:
        poly_coef[0] = noise - poly_coef[1] * 200
    else:
        poly_coef[0] = noise
    cdef double std = (lod - noise) / n_sigma
    return poly_coef, std

def getNoiseLODFromParam(DoubleArray2D params, double n_sigma):
    cdef double noise = params[0,0] / (math.sqrt(2*math.pi)*params[0,2])
    cdef double lod = noise + n_sigma*params[1,0]/(math.sqrt(2*math.pi)*params[1,2])
    return noise, lod

def updateNoiseLODParam(DoubleArray2D params, double n_sigma, double noise, double lod):
    params[0, 0] = noise * (math.sqrt(2*math.pi)*params[0,2])
    params[1, 0] = (lod-noise)*(math.sqrt(2*math.pi)*params[1,2]) / n_sigma
    return params

cdef DoubleArray noiseFunc(DoubleArray mass, DoubleArray poly_coef, DoubleArray2D norm_params, double[:] mass_points, int[:] mass_point_deltas):
    cdef np.ndarray[double, ndim=1] noise, tmp_noise
    cdef np.ndarray[cbool, ndim=1] mask
    cdef DoubleArray norm_param
    cdef int i
    noise = polynomial.polyval(mass, poly_coef)
    for i, norm_param in enumerate(norm_params, 1):
        mask = getMassPointMask(mass, mass_points[i-1], mass_point_deltas[i-1])
        tmp_noise = normFunc(mass[mask], norm_param[0], norm_param[1], norm_param[2])
        noise[mask] = np.maximum(noise[mask], tmp_noise)
    return noise
    

def getNoiseParams(DoubleArray mass, DoubleArray intensity, double quantile,
        cbool mass_dependent, double[:] mass_points, int[:] mass_point_deltas):
    cdef np.ndarray[cbool, ndim=1] is_peak, global_mask, other_mask, quantile_mask
    is_peak = getPeaksPositions(intensity)
    mass = mass[1:-1][is_peak]
    intensity = intensity[1:-1][is_peak]

    global_mask = getGlobalMask(mass)

    mass = mass[global_mask]
    intensity = intensity[global_mask]

    cdef np.ndarray[cbool, ndim=2] mass_masks = np.empty((mass_points.size, intensity.size), bool)
    cdef DoubleArray masked_mass, masked_intensity, poly_coef
    cdef double mass_point, std
    other_mask = np.ones(intensity.size, bool)
    # generate mask
    cdef int i
    for i, mass_point in enumerate(mass_points):
        mass_masks[i] = getMassPointMask(mass, mass_point, mass_point_deltas[i])
        other_mask &= ~mass_masks[i]

    masked_intensity = intensity[other_mask]
    
    if len(masked_intensity) == 0:
        poly_coef = np.zeros(2 if mass_dependent else 1, dtype=npdouble)
        std = 0
    else:
        quantile_mask = masked_intensity < np.quantile(masked_intensity, quantile)
        masked_mass = mass[other_mask][quantile_mask]
        masked_intensity = masked_intensity[quantile_mask]
        # poly
        if len(masked_mass) > 0:
            poly_coef = polynomial.polyfit(masked_mass,
                masked_intensity, 1 if mass_dependent else 0)
        else:
            poly_coef = np.zeros(2 if mass_dependent else 1)
        
        # norm
        std = masked_intensity.std()
    cdef list ret = []
    for i, mass_point in enumerate(mass_points):
        masked_mass = mass[mass_masks[i]]
        masked_intensity = intensity[mass_masks[i]]
        ret.append(getMassPointParams(masked_mass, masked_intensity, poly_coef,
            std, mass_point, mass_point_deltas[i]))
    return poly_coef, std, ret

cpdef tuple noiseLODFunc(DoubleArray mass, DoubleArray poly_coef,
        DoubleArray3D norm_params, double[:] mass_points, int[:] mass_point_deltas, double n_sigma):
    cdef DoubleArray noise, LOD
    noise = noiseFunc(mass, poly_coef, norm_params[:, 0], mass_points, mass_point_deltas)
    LOD = noise + n_sigma*noiseFunc(mass, poly_coef[:1], norm_params[:, 1], mass_points, mass_point_deltas)
    return noise, LOD

def getNoisePeaks(DoubleArray mass, DoubleArray intensity, DoubleArray poly_coef,
        DoubleArray3D norm_params, double[:] mass_point, int[:] mass_point_deltas,
        double n_sigma):
    cdef np.ndarray[cbool, ndim=1] is_peak = getPeaksPositions(intensity), mask
    mass = mass[1:-1][is_peak]
    intensity = intensity[1:-1][is_peak]

    _, LOD = noiseLODFunc(mass, poly_coef, norm_params, mass_point, mass_point_deltas, n_sigma)

    mask = intensity<LOD
    return mass[mask], intensity[mask]

def denoiseWithParams(DoubleArray mass, DoubleArray intensity, DoubleArray poly_coef,
        DoubleArray3D norm_params, double[:] mass_points, int[:] mass_point_deltas,
        double n_sigma, cbool subtract):
    cdef DoubleArray new_intensity, peak_mass, peak_intensity, noise, LOD
    cdef np.ndarray[cbool, ndim=1] is_peak = getPeaksPositions(intensity)
    cdef np.ndarray[np.int32_t, ndim=1] ind_peak
    cdef int length = mass.size

    ind_peak = np.arange(0, length, dtype=np.int32)[1:-1][is_peak]
    peak_mass = mass[1:-1][is_peak]
    peak_intensity = intensity[1:-1][is_peak]

    noise, LOD = noiseLODFunc(mass, poly_coef, norm_params, mass_points, mass_point_deltas, n_sigma)

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
    
    cdef np.ndarray[cbool, ndim=1] slt = getNotZeroPositions(new_intensity)
    return mass[slt], new_intensity[slt]
    