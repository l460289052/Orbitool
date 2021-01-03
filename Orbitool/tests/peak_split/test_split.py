# import h5py
import os
import sys
sys.path.append("C:/Users/l4602/OneDrive/Documents/Work/质谱分析/code")
import h5py
import numpy as np

import OrbitoolBase
import OrbitoolFunc


def split_peak(func: OrbitoolFunc.NormalDistributionFunc, peak: np.ndarray):
    peak = OrbitoolBase.Peak(None,None,peak[:,0],peak[:,1])    
    func.splitPeak(peak)


def test_split():
    func = OrbitoolFunc.NormalDistributionFunc([(1, 1, 1)])
    f = h5py.File("tests/peak_split/peaks.hdf5", 'r')
    for key in f:
        peak = f[key]
        func.peakSigmaFit = peak.attrs['sigma']
        split_peak(func, peak)

if __name__ == "__main__":
    test_split()