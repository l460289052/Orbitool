from typing import Dict, Tuple, Union, Iterable, List
from datetime import datetime

from sortedcontainers import SortedDict
import numpy as np
import h5py

from Orbitool.structures import HDF5

fileDtype = [
    ("path", h5py.string_dtype('utf-8')),
    ("creationDatetime", h5py.string_dtype()),
    ("startDatetime", h5py.string_dtype()),
    ("endDatetime", h5py.string_dtype())]

fileReader = None


def setFileReader(fr):
    global fileReader
    fileReader = fr


class FileList(HDF5.Group):
    h5_type = HDF5.RegisterType("FileList")
    files: HDF5.DataTable = HDF5.DataTable(fileDtype)

    def _crossed(self, start: datetime, end: datetime) -> Tuple[bool, str]:
        ds = self.files.dataset
        startDatetimes = ds['startDatetime'].astype('M8[s]')
        endDatetimes = ds['endDatetime'].astype('M8[s]')
        slt = (start < startDatetimes) & (endDatetimes < end)
        where = np.where(slt)
        if len(where) > 0:
            return False, ds[where]["path"]
        return True, None

    def timeRange(self):
        if len(self.files) == 0:
            return None, None
        ds = self.files.dataset
        startDatetimes = ds['startDatetime'].astype('M8[s]')
        endDatetimes = ds['endDatetime'].astype('M8[s]')
        return startDatetimes.min().astype(datetime), endDatetimes.min().astype(datetime)

    def addFile(self, filepath):
        f = fileReader(filepath)

        crossed, crossedFile = self._crossed(
            f.startDatetime, f.endDatetime)
        if crossed:
            raise ValueError('file "%s" and "%s" have crossed scan time' % (
                f.path, crossedFile.path))

        self.files.extend([(f.path, HDF5.Datetime.strftime(f.creationDatetime), HDF5.Datetime.strftime(
            f.creationDatetime + f.startTimedelta), HDF5.Datetime.strftime(f.creationDatetime + f.endTimedelta))])

    def rmFile(self, filepath: Union[str, Iterable]):
        files = self.files
        if isinstance(filepath, str):
            filepath = [filepath]
        ds = self.files.dataset
        path = ds['path']
        slt = np.zeros(len(ds), dtype=bool)
        for p in filepath:
            slt |= path == p
        ds[:slt.sum()] = ds[slt]
        ds.resize((slt.sum(),))

    def subList(self, filepath: List[str]):
        ds = self.files.dataset
        path = ds['path']
        slt = np.zeros(len(ds), dtype=bool)
        for p in filepath:
            slt |= path == p

        subList: FileList = FileList.create_at(HDF5.MemoryLocation(), 'tmp')
        subList.files.extend(ds[slt])

    def clear(self):
        self.files.clear()
        self.initialize()

    def __iter__(self):
        return iter(self.files.dataset[:])

    def __len__(self):
        return len(self.files.dataset)
