from typing import List
from Orbitool.utils.binary_search import indexBetween
from ._formula import Formula

from Orbitool.models import spectrum


def get_peak_position(peaks: List[spectrum.FittedPeak], index: int):
    return peaks[index].peak_position


def correct_formula(peak: spectrum.FittedPeak, peaks: List[spectrum.FittedPeak], rtol=1e-6) -> List[Formula]:
    formulas = []
    intensity = peak.peak_intensity
    for formula in peak.formulas:
        if not formula.isIsotope:
            formulas.append(formula)
            continue
        ratio = formula.relativeAbundance() * 1.5
        origin = formula.findOrigin()
        mz = origin.mass()
        s = indexBetween(peaks, (mz - mz * rtol, mz + mz * rtol),
                         method=get_peak_position)
        for p in peaks[s]:
            for f in p.formulas:
                if origin == f and p.peak_intensity * ratio > intensity:
                    formulas.append(formula)
                    continue
    return formulas
