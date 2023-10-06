from typing import List, Tuple

import numpy as np
from numpy.polynomial import polynomial

from Orbitool.base import (BaseDatasetStructure, BaseRowStructure,
                           BaseStructure, NdArray)

from ..formula import Formula, FormulaType, FormulaList
from .polynomial import polyfit_with_fixed_points


class Ion(BaseRowStructure):
    shown_text: str
    formula: FormulaType

    @classmethod
    def fromText(cls, text):
        return cls(shown_text=text, formula=Formula(text))

    def __eq__(self, other):
        assert isinstance(other, Ion)
        return self.formula == other.formula


class PathIonInfo(BaseDatasetStructure):
    raw_position: NdArray[float, -1]  # shape len(spectra)
    raw_intensity: NdArray[float, -1]  # shape len(spectra)

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
        return cls(
            raw_position=raw_position,
            raw_intensity=raw_intensity,
            position=position, rtol=rtol)


class Calibrator(BaseStructure):
    formulas: FormulaList = []
    used_indexes: NdArray[int, -1] = None
    unused_indexes: NdArray[int, -1] = None
    poly_coef: NdArray[float, -1] = None

    @classmethod
    def fromIonInfos(cls, ions: List[Ion], spectrum_ion_infos: List[PathIonInfo], use_N_ions: int, degree: int, start_point: Tuple[float, float] = None):
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
            points = np.zeros((0, 2), dtype=np.float64)
        else:
            points = np.array([start_point])
        poly_coef = polyfit_with_fixed_points(
            ions_position[used_indexes], ions_rtol[used_indexes], degree, points)
        return cls(
            formulas=[ion.formula for ion in ions],
            used_indexes=used_indexes, unused_indexes=unused_indexes,
            poly_coef=poly_coef)

    def predict_point(self, x: float):
        return polynomial.polyval(x, self.poly_coef)

    def predict_rtol(self, mz: np.ndarray):
        return polynomial.polyval(mz, self.poly_coef)

    def calibrate_mz(self, mz: np.ndarray):
        return mz * (1 - polynomial.polyval(mz, self.poly_coef))
