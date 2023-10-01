import numpy as np
from numpy import testing as nptest

from ..h5file import H5File
from ..extra_type_handlers.np_handler import NdArray
from ..dataset_structure import BaseDatasetStructure


def test_dataset_structure():
    class Spectrum(BaseDatasetStructure):
        index: NdArray[int, -1]
        mz: NdArray[float, -1]
        intensity:NdArray[float, -1]

        attr1: int
        attr2: str
    
    a = Spectrum(
        index=np.arange(10),
        mz=np.empty(10, dtype=float),
        intensity=np.empty(10, dtype=float),
        attr1=123,
        attr2="ddddddddddddddddddd")
    
    f = H5File()

    f.write("s", a)

    b = f.read("s", Spectrum)

    assert a == b
