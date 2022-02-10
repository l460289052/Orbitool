from datetime import datetime


import h5py
import numpy as np

from Orbitool.structures.HDF5.h5type_handlers.dict_handler import DictHandler
from Orbitool.utils.formula import Formula

from ..workspace import WorkSpace
from .base import register
from .utils import create_group, move_to, copy_to, read_dict, read_dict_keys, write_dict_keys, write_to


def update(path: str):
    """
    update to 2.1.5
    """
    with h5py.File(path, 'r+') as f:
        move_to(f, "file tab/raw_spectra", "noise tab/raw_spectra")
        copy_to(f, "file tab/info/spectrum_infos",
                "noise tab/info/denoised_spectrum_infos")
        f["noise tab/info"].attrs["to_be_calibrate"] = False

        info = f["calibration tab/info"]
        if len(info["calibrators"]):
            # only move ion infomations
            calibrator = info["calibrators"]["0"]
            copy_to(info, "calibrators/0/ions", "last_ions")

            path_times = {}
            for path in f["file tab/info/pathlist/paths"]:
                path_times[path['path'].decode()] = datetime.fromtimestamp(
                    path['createDatetime'])
            handler = DictHandler((str, datetime))
            handler.write_to_h5(info, "path_times", path_times)

            keys = read_dict_keys(info, "calibrators")
            path_ion_infos = write_dict_keys(info, "path_ion_infos", keys)
            for group, index, _ in read_dict(info, "calibrators"):
                index = str(index)
                calibrator: h5py.Group = group[index]
                ions_raw_position = calibrator["ions_raw_position"][:]
                ions_raw_intensity = calibrator["ions_raw_intensity"][:]
                ions_position = calibrator["ions_position"][:]
                ions_rtol = calibrator["ions_rtol"][:]

                ions = [Formula(formula.decode()) for formula in calibrator["ions"]["formula"]]
                ion_infos = write_dict_keys(path_ion_infos, index, ions)
                for ind, ion in enumerate(ions):
                    raw_position = ions_raw_position[:, ind]
                    raw_intensity = ions_raw_intensity[:, ind]
                    position = ions_position[ind]
                    rtol = ions_rtol[ind]

                    ion_group = create_group(ion_infos, ind)
                    write_to(ion_group, "raw_position", raw_position)
                    write_to(ion_group, "raw_intensity", raw_intensity)
                    ion_group.attrs["position"] = position
                    ion_group.attrs["rtol"] = rtol
                    ion_group.attrs["h5_type"] = "calibration path ion info"


register("2.1.5", update)
