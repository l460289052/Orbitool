from functools import lru_cache

import numpy as np
from h5py import Group

from ..utils.formula import Formula
from . import HDF5
from .HDF5 import BaseSingleConverter, register_converter


class FormulaConverter(BaseSingleConverter):
    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: Formula):
        h5group.attrs[key] = str(value)

    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        return Formula(h5group.attrs[key])
