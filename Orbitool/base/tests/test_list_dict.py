from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np

from .. import extra_type_handlers  # to register list & dict
from ..dataset_structure import BaseDatasetStructure
from ..extra_type_handlers.np_handler import NdArray
from ..h5file import H5File
from ..row_structure import BaseRowStructure
from ..structure import BaseStructure

from Orbitool.utils.formula import Formula, FormulaType


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


def test_list():

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


def test_dict():
    class Dicts(BaseStructure):
        simples: Dict[datetime, int] = {}
        rows: Dict[int, Row] = {}
        datasets: Dict[str, Spectrum] = {}
        structs: Dict[FormulaType, Struct] = {}

    rows = {i**2: Row(name=str(i), position=i * 1.5, time=datetime.now())
            for i in range(10)}
    datasets = {str(i): Spectrum(mz=np.empty(i, float), intensity=np.empty(
        i, float), time=datetime.now()) for i in range(10)}
    dicts_a = Dicts(
        simples={datetime.now()+timedelta(i): i for i in range(10)},
        rows=rows,
        datasets=datasets,
        structs={
            Formula(C=i, H=2 * i): Struct(row=row, spectrum=spectrum)
            for i, (row, spectrum) in enumerate(zip(rows.values(), datasets.values()))})

    f = H5File()
    f.write("s", dicts_a)

    dicts_b = f.read("s", Dicts)

    assert dicts_a.simples == dicts_b.simples
    assert dicts_a.rows == dicts_b.rows
    assert dicts_a.datasets == dicts_b.datasets
    assert dicts_a.structs == dicts_b.structs
