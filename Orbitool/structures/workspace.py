import os
import tempfile
from datetime import datetime
import h5py
from typing import Union


from . import HDF5, spectrum
from .file import FileList, setFileReader, SpectrumInfo

from Orbitool import config
from Orbitool.utils import readers

setFileReader(readers.ThermoFile)


class SpectraList(HDF5.Group):
    h5_type = HDF5.RegisterType("SpectraList")

    file_spectrum_info_list = HDF5.datatable.Datatable.descriptor(SpectrumInfo)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_start_time :datetime= None


class NoiseTab(HDF5.Group):
    h5_type = HDF5.RegisterType("NoiseTab")

    current_spectrum: spectrum.Spectrum = spectrum.Spectrum.descriptor()


class WorkSpace(HDF5.File):
    h5_type = HDF5.RegisterType("Orbitool_Workspace")

    file_list: FileList = FileList.descriptor()
    spectra_list: SpectraList = SpectraList.descriptor()
    noise_tab: NoiseTab = NoiseTab.descriptor()

    def close(self):
        self.location.close()
