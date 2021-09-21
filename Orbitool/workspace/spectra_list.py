from array import array
from ..structures import BaseStructure, field
from ..structures.HDF5 import Array


class SpectraListInfo(BaseStructure):
    h5_type = "spectra list info"

    shown_indexes: Array(int) = field(default_factory=lambda: array('i'))
