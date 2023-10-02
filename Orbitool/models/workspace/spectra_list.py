from array import array
from ..structures import BaseStructure, field
from ..structures.HDF5 import Array
from .base import BaseInfo


class SpectraListInfo(BaseInfo):
    h5_type = "spectra list info"

    shown_indexes: Array(int) = field(default_factory=lambda: array('i'))
