from copy import deepcopy
from typing import Iterable, List, Dict, Union
import math
import itertools

import numpy as np

from ..functions.calibration import Ion, Calibrator, PolynomialRegressionFunc
from ..utils.formula import Formula
from ..structures import BaseStructure, BaseRowItem, field, Row
from ..structures.spectrum import Spectrum, SpectrumInfo
from ..structures.HDF5 import StructureList
from .base import Widget as BaseWidget


def default_ions():
    return list(map(Ion.fromText,
                    ["HNO3NO3-", "C6H3O2NNO3-", "C6H5O3NNO3-",
                     "C6H4O5N2NO3-", "C8H12O10N2NO3-", "C10H17O10N3NO3-"]))


class CalibratorInfoSegment(BaseStructure):
    h5_type = "calibrator info segment"

    # info
    end_point: float = math.inf

    shown_rtol: float = 2e-6
    shown_degree: int = 2
    shown_n_ions: int = 3
    shown_ions: Row[Ion] = field(list)

    rtol: float = None
    degree: int = None
    n_ions: int = None
    ions: Row[Ion] = field(list)

    def need_split(self):
        return abs(self.shown_rtol / self.rtol - 1) > 1e-6 \
            or self.shown_ions != self.ions

    def need_calibrate(self):
        return self.need_split() \
            or self.shown_degree != self.degree \
            or self.shown_n_ions != self.n_ions

    def add_ions(self, ions: Iterable[Ion]):
        s = {ion.formula for ion in self.shown_ions}
        for ion in ions:
            if ion.formula in s:
                continue
            self.shown_ions.append(ion)
        self.shown_ions.sort(key=lambda ion: ion.formula.mass())


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    skip: bool = False

    current_segment_index: int = 0

    calibrate_info_segments: List[CalibratorInfoSegment] = field(
        lambda: [CalibratorInfoSegment(shown_ions=default_ions())])
    calibrator_segments: Dict[str, List[Calibrator]] = field(dict)
    calibrated_spectrum_infos: Row[SpectrumInfo] = field(list)

    def add_segment(self, separator: float):
        pos = 0
        segments = self.calibrate_info_segments
        while len(segments) > pos and segments[pos].end_point < separator:
            pos += 1
        if segments[pos].end_point == separator:
            raise ValueError("repeat separator")
        old_segment = segments[pos]
        new_segment = deepcopy(old_segment)
        new_segment.end_point = separator
        for ind, ion in reversed(list(enumerate(old_segment.shown_ions.copy()))):
            if ion.formula.mass() < separator:
                old_segment.shown_ions.pop(ind)
        for ind, ion in reversed(list(enumerate(new_segment.shown_ions.copy()))):
            if ion.formula.mass() > separator:
                new_segment.shown_ions.pop(ind)
        self.calibrate_info_segments.insert(
            pos, new_segment)

    def merge_segment(self, begin: int, end: int):
        segments = self.calibrate_info_segments[begin:end]
        new_segment = deepcopy(segments[0])
        new_segment.end_point = segments[-1].end_point
        for seg in segments[1:]:
            new_segment.add_ions([ion.shown_text for ion in seg.shown_ions])
        self.calibrate_info_segments[begin:end] = [new_segment]

    def add_ions(self, str_ions: List[str]):
        ions = [Ion.fromText(ion) for ion in str_ions]
        for cali_info in self.calibrate_info_segments:
            slt = [ion.formula.mass() < cali_info.end_point for ion in ions]
            slt = np.array(slt, dtype=bool)
            cali_info.add_ions(itertools.compress(ions, slt))
            ions = list(itertools.compress(ions, ~slt))


class Widget(BaseWidget[CalibratorInfo]):
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
