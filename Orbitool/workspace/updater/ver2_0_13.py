import numpy as np

from ..workspace import WorkSpace
from .base import register


def update(workspace: WorkSpace):
    info = workspace.peakfit_tab.info
    if info.spectrum is not None:
        peaks = [(peak.mz, peak.intensity) for peak in info.raw_peaks]
        info.shown_mz = np.concatenate([mz for mz, _ in peaks])
        info.shown_intensity = np.concatenate(
            [intensity for _, intensity in peaks])
        info.shown_residual = info.residual_intensity


register("2.0.13", update)
