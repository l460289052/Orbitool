import numpy as np
import h5py

from .base import register
from .utils import write_to


def update(path: str):
    with h5py.File(path, 'r+') as f:
        info = f["peak fit tab/info"]
        peaks = [(peak['mz'], peak['intensity']) for peak in info['raw_peaks']]

        write_to(info, "shown_mz", np.concatenate([mz for mz, _ in peaks]))
        write_to(info, "shown_intensity", np.concatenate(
            [intensity for _, intensity in peaks]))
        write_to(info, "shown_residual", info["residual_intensity"])


register("2.0.13", update)
