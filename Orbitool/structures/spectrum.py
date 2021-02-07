from . import HDF5


class Peak(HDF5.Group):
    h5_type = HDF5.RegisterType("Peak")
    mz = HDF5.SmallNumpy()
    intensity = HDF5.SmallNumpy()
    splitNum = HDF5.Int()


class FittedPeak(Peak):
    h5_type = HDF5.RegisterType("FittedPeak")

    fitted_param = HDF5.SmallNumpy()
    peak_position = HDF5.SmallNumpy()
    peak_intensity = HDF5.SmallNumpy()
    formula_list = HDF5.LightList.descriptor()


class Spectrum(HDF5.Group):
    h5_type = HDF5.RegisterType("Spectrum")

    file_path = HDF5.Str()
    mass = HDF5.BigNumpy()
    intensity = HDF5.BigNumpy()
    start_tTime = HDF5.Datetime()
    end_time = HDF5.Datetime()


class SpectrumList(HDF5.Group):
    h5_type = HDF5.RegisterType("SpectrumList")


# class MassListItem
