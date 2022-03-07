from copy import deepcopy
from datetime import datetime
from typing import Iterable, List, Dict, Tuple, Union
import math

import numpy as np

from ..functions.calibration import Ion, PathIonInfo, Calibrator
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
    last_ions: Row[Ion] = field(list)

    calibrate_info_segments: List[CalibratorInfoSegment] = field(
        lambda: [CalibratorInfoSegment()])
    last_calibrate_info_segments: List[CalibratorInfoSegment] = field(list)

    path_times: Dict[str, datetime] = field(dict)
    path_ion_infos: Dict[str, Dict[Formula, PathIonInfo]] = field(dict)
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

    def yield_segment_ions(self):
        ret_ions: List[Ion] = []
        ion_right = 0
        ions = self.ions
        for seg in self.calibrate_info_segments:
            while ion_right < len(ions) and ions[ion_right].formula.mass() < seg.end_point:
                ret_ions.append(ions[ion_right])
                ion_right += 1
            yield seg, ret_ions
            ret_ions = []

    def yield_ion_used(self, path: str):
        if path in self.calibrator_segments:
            calibrators = self.calibrator_segments[path]
            formula_ions = {ion.formula: ion for ion in self.last_ions}
            for calibrator in calibrators:
                for index, formula in enumerate(calibrator.formulas):
                    yield formula_ions[formula], index in calibrator.used_indexes
        else:  # fail to calibrate
            for ion in self.last_ions:
                yield ion, False

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
        last_formulas = {ion.formula for ion in self.last_ions}
        need_split = [
            ion.formula for ion in self.ions if ion.formula not in last_formulas]
        return need_split

    def done_split(self, path_ions_peak: Dict[str, List[List[Tuple[float, float]]]]):
        """
            path_ions_peak: {path: [[(position, intensity) for each ion] for each spectrum in path]}
        """
        formulas = self.need_split()
        for path, ions_peak in path_ions_peak.items():
            ion_infos = self.path_ion_infos.setdefault(path, {})
            # shape: (len(spectra), len(ions), 2)
            ions_peak = np.array(ions_peak, dtype=np.float64)
            for index, formula in enumerate(formulas):
                ion_infos[formula] = PathIonInfo.fromRaw(
                    formula,
                    ions_peak[:, index, 0],
                    ions_peak[:, index, 1])
        self.last_ions = self.ions.copy()

    def calc_calibrator(self):
        self.calibrator_segments.clear()

        segment_ions = list(self.yield_segment_ions())
        for path, ion_infos in self.path_ion_infos.items():
            try:
                calibrators = []

                start_point = None
                for seg_info, ions in segment_ions:
                    cali = Calibrator.fromIonInfos(
                        ions,
                        [ion_infos[ion.formula] for ion in ions],
                        seg_info.n_ions,
                        seg_info.degree,
                        start_point)
                    start_point = (seg_info.end_point,
                                cali.predict_point(seg_info.end_point))
                    calibrators.append(cali)
                self.calibrator_segments[path] = calibrators
            except Exception as e:
                raise ValueError(f"Error at file {path}") from e
        self.last_calibrate_info_segments = deepcopy(
            self.calibrate_info_segments)


class Widget(BaseWidget[CalibratorInfo]):
    calibrated_spectra = StructureList(Spectrum)

    def __init__(self, obj) -> None:
        super().__init__(obj, CalibratorInfo)
