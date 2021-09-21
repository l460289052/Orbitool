from ....structures import base, HDF5
from .normal_distribution import NormalDistributionFunc


class NormalDistributionFuncStructure(base.BaseStructure):
    h5_type = "normal distribution func"

    peak_fit_sigma: float
    peak_fit_res: float


class Converter(HDF5.BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group, key: str, value: NormalDistributionFunc):
        struct = NormalDistributionFuncStructure(
            peak_fit_sigma=value.peak_fit_sigma, peak_fit_res=value.peak_fit_res)
        HDF5.StructureHandler.write_to_h5(h5group, key, struct)

    @staticmethod
    def read_from_h5(h5group, key: str):
        struct: NormalDistributionFuncStructure = HDF5.StructureHandler.read_from_h5(
            h5group, key)
        func = NormalDistributionFunc(
            struct.peak_fit_sigma, struct.peak_fit_res)
        return func

HDF5.register_converter(NormalDistributionFunc, Converter)