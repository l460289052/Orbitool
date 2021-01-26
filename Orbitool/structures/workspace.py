import os
import tempfile
from datetime import datetime
import h5py


from . import HDF5
from .file import FileList, setFileReader

from Orbitool import config
from Orbitool.utils import readers

setFileReader(readers.ThermoFile)


class WorkSpace:
    def __init__(self, path=None) -> None:
        if path is None:
            self.tempDir = tempfile.TemporaryDirectory(
                prefix=datetime.now().strftime(config.TempFile.prefixTimeFormat), dir=config.TempFile.tempPath)
            self.h5 = h5py.File(os.path.join(
                self.tempDir.name, 'tmp.hdf5'), 'a')
        else:
            self.tempDir = None
            self.h5 = h5py.File(path, 'a')

        self.fileList: FileList = FileList.openOrCreateInitialize(
            self.h5, 'fileList')
        
    def close(self):
        self.h5.close()