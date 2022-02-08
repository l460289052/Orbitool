import heapq
from datetime import datetime
from typing import List, Tuple

import numpy as np
from numpy.polynomial import polynomial

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


class Calibrator(BaseStructure):
    """
        ions_raw_position: shape (len(spectrum), len(ions))
        ions_raw_intensity: shape (len(spectrum), len(ions))

        ions_position: shape (len(ions))
        ions_rtol: shape (len(ions))
    """
    h5_type = "calibrator"

    time: datetime
    ions: Row[Ion]
    ions_raw_position: np.ndarray
    ions_raw_intensity: np.ndarray

    ions_position: np.ndarray
    ions_rtol: np.ndarray

    used_indexes: np.ndarray = None
    unused_indexes: np.ndarray = None
    poly_coef: np.ndarray = None

    @classmethod
    def fromMzInt(cls, time: datetime, ions: List[Ion], ions_raw_position: np.ndarray, ions_raw_intensity: np.ndarray):
        """
        ions_raw_position: shape (len(spectrum), len(ions))
        ions_raw_intensity: shape (len(spectrum), len(ions))
        """
        ions_mz = np.fromiter([ion.formula.mass()
                               for ion in ions], dtype=float)
        ions_position = []
        for index, ion in enumerate(ions_mz):
            position: np.ndarray = ions_raw_position[:, index]
            select = ~np.isnan(position)
            if select.sum():
                ions_position.append(position[select].mean())
            else:
                ions_position.append(np.nan)

        ions_position = np.array(ions_position, dtype=float)

        ions_rtol: np.ndarray = 1 - ions_mz / ions_position

        return Calibrator(time, ions, ions_raw_position, ions_raw_intensity, ions_position,
                          ions_rtol)

    def regeneratCalibrator(self, use_N_ions=None):
        return self.fromMzInt(self.time, self.ions, self.ions_raw_position, self.ions_raw_intensity, rtol, use_N_ions)

    def fit(self, use_N_ions: int, degree: int, last_point: Tuple[float, float]):
        ions_rtol = self.ions_rtol
        length = len(ions_rtol)
        if length < use_N_ions:
            use_N_ions = length

        abs_rtol_minarg = abs(ions_rtol).argsort()
        used_indexes = abs_rtol_minarg[:use_N_ions]
        unused_indexes = abs_rtol_minarg[use_N_ions:]

        if any(np.isnan(ions_rtol[used_indexes])):
            missing = [ion.shown_text for ion, slt in zip(
                self.ions, np.isnan(ions_rtol)) if slt]
            raise ValueError(
                f"Cannot find enough ions to fit, missing ions: {missing}")
        self.used_indexes = used_indexes
        self.unused_indexes = unused_indexes

        raise NotImplementedError()
        self.poly_coef = ...  

    def predict_rtol(self, mz: np.ndarray):
        assert self.poly_coef is not None
        return polynomial.polyval(mz, self.poly_coef)

    def calibrate_mz(self, mz: np.ndarray):
        assert self.poly_coef is not None
        return mz * (1 - polynomial.polyval(mz, self.poly_coef))
