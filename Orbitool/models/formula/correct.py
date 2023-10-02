from typing import List
from ..binary_search import indexBetween
from ...models.spectrum.spectrum import Formula, FittedPeak


def get_peak_position(peaks, index):
    return peaks[index].peak_position


def correct_formula(peak: FittedPeak, peaks: List[FittedPeak], rtol=1e-6) -> List[Formula]:
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
