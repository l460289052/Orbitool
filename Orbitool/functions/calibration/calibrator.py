import heapq
from datetime import datetime
from typing import List, Tuple

import numpy as np
from numpy.polynomial import polynomial

from .polynomial import polyfit_with_fixed_points
from ...structures.HDF5 import NdArray
from ...structures import BaseStructure, BaseRowItem, Row
from ...structures.spectrum import Spectrum
from ...utils.formula import Formula


class Ion(BaseRowItem):
    item_name = "calibration ion"

    shown_text: str
    formula: Formula

    @classmethod
    def fromText(cls, text):
        return Ion(text, Formula(text))

    def __eq__(self, other):
        assert isinstance(other, Ion)
        return self.formula == other.formula


class SpectrumIonInfo(BaseRowItem):
    item_name = "calibration spectrum ion info"

    raw_position: NdArray[float, -1]
    raw_intensity: NdArray[float, -1]

    position: float
    rtol: float

    @classmethod
    def fromRaw(cls, formula: Formula, raw_position: np.ndarray, raw_intensity: np.ndarray):
        mass = formula.mass()
        slt = ~np.isnan(raw_position)
        if slt.sum():
            position = raw_position[slt].mean()
        else:
            position = np.nan
        rtol = 1 - mass / position
        return cls(raw_position, raw_intensity, position, rtol)


class Calibrator(BaseStructure):
    """
        ions_raw_position: shape (len(spectrum), len(ions))
        ions_raw_intensity: shape (len(spectrum), len(ions))

        ions_position: shape (len(ions))
        ions_rtol: shape (len(ions))
    """
    h5_type = "calibrator"

    time: datetime

    used_indexes: np.ndarray = None
    unused_indexes: np.ndarray = None
    poly_coef: np.ndarray = None

    @classmethod
    def fromIonInfos(cls, ions: List[Ion], spectrum_ion_infos: List[SpectrumIonInfo], time: datetime, use_N_ions: int, degree: int, start_point: Tuple[float, float] = None):
        ions_position = np.array(
            [info.position for info in spectrum_ion_infos])
        ions_rtol = np.array([info.rtol for info in spectrum_ion_infos])
        length = len(ions_rtol)
        if length < use_N_ions:
            use_N_ions = length

        abs_rtol_minarg = abs(ions_rtol).argsort()
        used_indexes = abs_rtol_minarg[:use_N_ions]
        unused_indexes = abs_rtol_minarg[use_N_ions:]

        if any(np.isnan(ions_rtol[used_indexes])):
            missing = [ion.shown_text for ion, slt in zip(
                ions, np.isnan(ions_rtol)) if slt]
            raise ValueError(
                f"Cannot find enough ions to fit, missing ions: {missing}")
        if start_point is None:
            points = []
        else:
            points = [start_point]
        poly_coef = polyfit_with_fixed_points(
            ions_position, ions_rtol, degree, np.array(points))
        return cls(time, used_indexes, unused_indexes, poly_coef)

    def predict_rtol(self, mz: np.ndarray):
        assert self.poly_coef is not None
        return polynomial.polyval(mz, self.poly_coef)

    def calibrate_mz(self, mz: np.ndarray):
        assert self.poly_coef is not None
        return mz * (1 - polynomial.polyval(mz, self.poly_coef))
