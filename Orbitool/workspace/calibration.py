from copy import deepcopy
from typing import Iterable, List, Dict, Tuple, Union
import math
import itertools

import numpy as np


from ..functions.calibration import Ion, SpectrumIonInfo, Calibrator, PolynomialRegressionFunc
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

    end_point: float = math.inf

    degree: int = 2
    n_ions: int = 3


class CalibratorInfo(BaseStructure):
    h5_type = "calibrator tab"

    skip: bool = False

    current_segment_index: int = 0

    rtol: float = 2e-6
    ions: Row[Ion] = field(default_ions)

    spectrum_ion_infos: Row[SpectrumIonInfo] = field(list)
    calibrate_info_segments: List[CalibratorInfoSegment] = field(
        lambda: [CalibratorInfoSegment()])
    last_calibrate_info_segments: List[CalibratorInfoSegment] = field(list)
    calibrator_segments: Dict[str, List[Calibrator]] = field(
        dict)  # path -> [calibrator for each segments]
    calibrated_spectrum_infos: Row[SpectrumInfo] = field(
        list)  # [calibrated spectrum info for each spectrum]

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
        self.calibrate_info_segments.insert(
            pos, new_segment)

    def merge_segment(self, begin: int, end: int):
        segments = self.calibrate_info_segments[begin:end]
        self.calibrate_info_segments[begin:end] = segments[-1:]

    def get_ions_for_segment(self, segment_index: int) -> List[Ion]:
        left = 0
        if segment_index:
            begin_point = self.calibrate_info_segments[segment_index - 1].end_point
            while left < len(self.ions) and self.ions[left].formula.mass() < begin_point:
                left += 1
        right = left
        end_point = self.calibrate_info_segments[segment_index].end_point
        while right < len(self.ions) and self.ions[right].formula.mass() < end_point:
            right += 1
        return self.ions[left:right]

    def add_ions(self, str_ions: List[str]):
        ions = [Ion.fromText(ion) for ion in str_ions]
        s = {ion.formula for ion in self.ions}
        for ion in ions:
            if ion.formula in s:
                continue
            self.ions.append(ion)
        self.ions.sort(key=lambda ion: ion.formula.mass())

    def need_split(self) -> List[Formula]:
        """
            return [formula for each ion need to be split]
        """

        pass

    def done_split(self, path_ions_peak: Dict[str, List[List[Tuple[float, float]]]]):
        """
            path_ions_peak: {path: [[(position, intensity) for each ion] for each spectrum in path]}
        """
        pass

    def need_calibrate(self):
        pass

    def done_calibrate(self):
        pass


class Widget(BaseWidget[CalibratorInfo]):
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
