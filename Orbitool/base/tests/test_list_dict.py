from datetime import datetime
from typing import List

import numpy as np

from .. import extra_type_handlers # to register list & dict
from ..dataset_structure import BaseDatasetStructure
from ..extra_type_handlers.np_handler import NdArray
from ..h5file import H5File
from ..row_structure import BaseRowStructure
from ..structure import BaseStructure


def test_list():
    class Row(BaseRowStructure):
        name: str
        position: float
        time: datetime

    class Spectrum(BaseDatasetStructure):
        mz: NdArray[float, -1]
        intensity: NdArray[float, -1]
        time: datetime

    class Struct(BaseStructure):
        row: Row
        spectrum: Spectrum

    class Lists(BaseStructure):
        simples: List[int] = []
        rows: List[Row] = []
        datasets: List[Spectrum] = []
        structs: List[Struct] = []

    rows = [Row(name=str(i), position=i * 1.5, time=datetime.now())
            for i in range(10)]
    datasets = [Spectrum(mz=np.empty(i, float), intensity=np.empty(
        i, float), time=datetime.now()) for i in range(10)]
    lists_a = Lists(
        simples=range(10),
        rows=rows,
        datasets=datasets,
        structs=[Struct(
            row=row, spectrum=spectrum) for row, spectrum in zip(rows, datasets)])
    
    f = H5File()
    f.write("s", lists_a)

    lists_b = f.read("s", Lists)

    assert lists_a.simples == lists_b.simples
    assert lists_a.rows == lists_b.rows
    assert lists_a.datasets == lists_b.datasets
    assert lists_a.structs == lists_b.structs
    
