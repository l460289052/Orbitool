from ... import HDF5
import numpy as np
import h5py

type_name = 'testSpectrum'


class Spectrum(HDF5.Group):
    h5_type = HDF5.RegisterType(type_name)
    mz = HDF5.SmallNumpy()
    intensity = HDF5.BigNumpy()
    time = HDF5.Datetime()

    father = HDF5.Ref_Attr('testSpectra')

    def initialize(self, mz, intensity, time):
        self.mz = mz
        self.intensity = intensity
        self.time = time

class Spectra(HDF5.Group):
    h5_type = HDF5.RegisterType('testSpectra')
    spectra: HDF5.List = HDF5.List.descriptor(Spectrum)
