import os
import tempfile
from datetime import datetime
import h5py
from typing import Union

import numpy as np

from . import HDF5, spectrum
from .formula import DatatableDescriptor as FormulaDatatableDescriptor
from .file import FileList, setFileReader, SpectrumInfo

from Orbitool import config
from Orbitool.utils import readers
from Orbitool.utils.formula import Formula

setFileReader(readers.ThermoFile)


class SpectraList(HDF5.Group):
    h5_type = HDF5.RegisterType("SpectraList")

    file_spectrum_info_list = HDF5.datatable.Datatable.descriptor(SpectrumInfo)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_start_time: datetime = None


class NoiseFormulaParameter(HDF5.datatable.DatatableItem):
    item_name = "NoiseFormulaParameter"
    formula: Formula = FormulaDatatableDescriptor()
    delta: float = HDF5.datatable.Float64()

    selected: bool = HDF5.datatable.Bool()
    param = HDF5.datatable.Ndarray2D(float, 3)


class NoiseTab(HDF5.Group):
    h5_type = HDF5.RegisterType("NoiseTab")

    current_spectrum: spectrum.Spectrum = spectrum.Spectrum.descriptor()
    noise_formulas = HDF5.datatable.Datatable.descriptor(NoiseFormulaParameter)

    n_sigma = HDF5.Float()
    poly_coef = HDF5.SimpleDataset()
    global_noise_std = HDF5.Float()
    noise = HDF5.SimpleDataset()
    LOD = HDF5.SimpleDataset()

    def initialize(self):
        self.noise_formulas.initialize()

        self.noise_formulas.extend([NoiseFormulaParameter(
            Formula(f), 5, False, np.zeros((2, 3))) for f in config.noise_formulas])


class WorkSpace(HDF5.File):
    h5_type = HDF5.RegisterType("Orbitool_Workspace")

    file_list: FileList = FileList.descriptor()
    spectra_list: SpectraList = SpectraList.descriptor()
    noise_tab: NoiseTab = NoiseTab.descriptor()

    def close(self):
        self.location.close()
