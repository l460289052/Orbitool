from h5py import Group

from ....structures import (BaseStructure, StructureTypeHandler, get_handler,
                            register_handler)
from .normal_distribution import NormalDistributionFunc


class NormalDistributionFuncStructure(BaseStructure):
    h5_type = "normal distribution func"

    peak_fit_sigma: float
    peak_fit_res: float


class Handler(StructureTypeHandler):
    def write_to_h5(self, h5group: Group, key: str, value: NormalDistributionFunc):
        struct = NormalDistributionFuncStructure(
            value.peak_fit_sigma, value.peak_fit_res)
        handler: StructureTypeHandler = get_handler(
            NormalDistributionFuncStructure)
        handler.write_to_h5(h5group, key, struct)

    def read_from_h5(self, h5group: Group, key: str):
        handler: StructureTypeHandler = get_handler(
            NormalDistributionFuncStructure)
        struct: NormalDistributionFuncStructure = handler.read_from_h5(
            h5group, key)
        func = NormalDistributionFunc(
            struct.peak_fit_sigma, struct.peak_fit_res)
        return func

register_handler(NormalDistributionFunc, Handler)