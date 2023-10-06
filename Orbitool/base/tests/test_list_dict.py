from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Set

import numpy as np

from .. import extra_type_handlers  # to register list & dict
from ..dataset_structure import BaseDatasetStructure
from ..extra_type_handlers.np_handler import NdArray
from ..extra_type_handlers.seq_handler import AttrList
from ..h5file import H5File
from ..row_structure import BaseRowStructure
from ..structure import BaseStructure

from Orbitool.models.formula import Formula, FormulaType


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


def t_seq(typ):
    class Lists(BaseStructure):
        simples: typ[int] = []
        rows: typ[Row] = []
        datasets: typ[Spectrum] = []
        structs: typ[Struct] = []

        attr1: AttrList[datetime] = []
        attr2: AttrList[str] = []

    rows = [Row(name=str(i), position=i * 1.5, time=datetime.now())
            for i in range(10)]
    datasets = [Spectrum(mz=np.empty(i, float), intensity=np.empty(
        i, float), time=datetime.now()) for i in range(10)]
    lists_a = Lists(
        simples=range(10),
        rows=rows,
        datasets=datasets,
        structs=[Struct(
            row=row, spectrum=spectrum) for row, spectrum in zip(rows, datasets)],
        attr1=[datetime.now()] * 10,
        attr2=list(map(str, range(10))))

    f = H5File()
    f.write("s", lists_a)
    assert f._obj["s"].attrs["attr1"] is not None

    lists_b = f.read("s", Lists)

    assert lists_a.simples == lists_b.simples
    assert lists_a.rows == lists_b.rows
    assert lists_a.datasets == lists_b.datasets
    assert lists_a.structs == lists_b.structs
    assert lists_a.attr1 == lists_b.attr1
    assert lists_a.attr2 == lists_b.attr2


def test_list():
    t_seq(List)


def test_deque():
    t_seq(Deque)


def test_set():
    class Sets(BaseStructure):
        simples: Set[int] = set()

    sets_a = Sets(simples=range(10))

    f = H5File()
    f.write("s", sets_a)

    sets_b = f.read("s", Sets)

    assert sets_a.simples == sets_b.simples


def test_list_list():
    class Lists(BaseStructure):
        simples: List[List[int]] = []
        datasets: List[List[Spectrum]] = []

    lists_a = Lists(
        simples=[list(range(i)) for i in range(10)],
        datasets=[[Spectrum(mz=np.empty(j, float), intensity=np.empty(
            j, float), time=datetime.now()) for j in range(i)] for i in range(10)])

    f = H5File()
    f.write("s", lists_a)

    lists_b = f.read("s", Lists)

    assert lists_a.simples == lists_b.simples
    assert lists_a.datasets == lists_b.datasets


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
        simples={datetime.now() + timedelta(i): i for i in range(10)},
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


def test_dict_cell_shape():
    class Cell(BaseRowStructure):
        a: int
        b: NdArray[float, (2, 3)]

    class D(BaseStructure):
        rows: Dict[str, Cell] = {}

    a = D(rows={
        str(i): Cell(a=i, b=np.ones((2, 3), dtype=float))
        for i in range(10)
    })

    f = H5File()
    f.write("d", a)
    b = f.read("d", D)

    assert a == b
