from Orbitool.structures import HDF5

type_name = 'Spectrum'


class Spectrum(HDF5.Group):
    h5_type = HDF5.RegisterType(type_name)
    mz = HDF5.SmallNumpy()
    intensity = HDF5.BigNumpy()
    time = HDF5.Datetime()

    def initialize(self, mz, intensity, time):
        self.mz = mz
        self.intensity = intensity
        self.time = time

class Spectra(HDF5.Group):
    h5_type = HDF5.RegisterType('Spectra')
    spectra: HDF5.List = HDF5.List.descriptor(Spectrum)