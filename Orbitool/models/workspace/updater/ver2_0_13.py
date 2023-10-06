import numpy as np
import h5py

from .utils import write_to


def update(f: h5py.File):
    info = f["peak fit tab/info"]
    peaks = [(peak['mz'], peak['intensity']) for peak in info['raw_peaks']]

    write_to(info, "shown_mz", np.concatenate([mz for mz, _ in peaks]))
    write_to(info, "shown_intensity", np.concatenate(
        [intensity for _, intensity in peaks]))
    write_to(info, "shown_residual", info["residual_intensity"])

