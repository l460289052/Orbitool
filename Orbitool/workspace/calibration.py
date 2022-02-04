from copy import deepcopy
from typing import List, Dict, Union
import math

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


class CalibratorSegment(BaseStructure):
    h5_type = "calibrator segment"

    # info
    end_point: float = math.inf
    ions: Row[Ion] = field(list)

    rtol: float = 2e-6
    degree: int = 2
    n_ions: int = 3

    # result
    calibrators: Dict[str, Calibrator] = field(dict)
    poly_funcs: Dict[str, PolynomialRegressionFunc] = field(dict)
    calibrated_spectrum_infos: Row[SpectrumInfo] = field(list)

    def add_ions(self, ions: List[str]):
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            i = Ion.fromText(ion)
            if i.formula in s:
                continue
            self.ions.append(i)
        self.ions.sort(key=lambda ion: ion.formula.mass())


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    skip: bool = False

    current_segment_index: int = 0

    calibrator_segments: List[CalibratorSegment] = field(
        lambda: [CalibratorSegment(ions=default_ions())])

    def add_segment(self, separator: float):
        pos = 0
        segments = self.calibrator_segments
        while len(segments) > pos and segments[pos].end_point < separator:
            pos += 1
        if segments[pos].end_point == separator:
            raise ValueError("repeat separator")
        old_segment = segments[pos]
        new_segment = deepcopy(old_segment)
        new_segment.end_point = separator
        for ind, ion in reversed(list(enumerate(old_segment.ions.copy()))):
            if ion.formula.mass() < separator:
                old_segment.ions.pop(ind)
        for ind, ion in reversed(list(enumerate(new_segment.ions.copy()))):
            if ion.formula.mass() > separator:
                new_segment.ions.pop(ind)
        self.calibrator_segments.insert(
            pos, new_segment)

    def merge_segment(self, begin: int, end: int):
        segments = self.calibrator_segments[begin:end]
        new_segment = deepcopy(segments[0])
        new_segment.end_point = segments[-1].end_point
        for seg in segments[1:]:
            new_segment.add_ions([ion.shown_text for ion in seg.ions])
        self.calibrator_segments[begin:end] = [new_segment]

    def add_ions(self, ions: List[str]):
        pass


class Widget(BaseWidget[CalibratorInfo]):
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
