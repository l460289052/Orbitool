from typing import Dict, Tuple, Union, Iterable, List
from datetime import datetime

from sortedcontainers import SortedDict
import numpy as np
import h5py

from Orbitool.structures import HDF5
from Orbitool.structures.HDF5 import datatable


class File(datatable.DatatableItem):
    item_name = "File"

    path = datatable.str_utf8()
    createDatetime = datatable.Datetime64s()
    startDatetime = datatable.Datetime64s()
    endDatetime = datatable.Datetime64s()


fileReader = None


def setFileReader(fr):
    global fileReader
    fileReader = fr


class FileList(HDF5.Group):
    h5_type = HDF5.RegisterType("FileList")
    files: datatable.Datatable = datatable.Datatable.descriptor(File)

    def _crossed(self, start: datetime, end: datetime) -> Tuple[bool, str]:
        startDatetimes = self.files.get_column("startDatetime")
        endDatetimes = self.files.get_column("endDatetime")
        slt = (start < startDatetimes) & (endDatetimes < end)
        where = np.where(slt)
        if len(where) > 0:
            return False, list(self.files[where])
        return True, None

    def timeRange(self):
        if len(self.files) == 0:
            return None, None
        startDatetimes = self.files.get_column("startDatetime")
        endDatetimes = self.files.get_column("endDatetime")
        return startDatetimes.min().astype(datetime), endDatetimes.max().astype(datetime)

    def addFile(self, filepath):
        f = fileReader(filepath)

        crossed, crossedFiles = self._crossed(
            f.startDatetime, f.endDatetime)
        if crossed:
            raise ValueError(
                f'file "{f.path}" and "{[f.path for f in crossedFiles]}" have crossed scan time')

        file = File(f.path, f.creationDatetime, f.creationDatetime +
                    f.startTimedelta, f.creationDatetime + f.endTimedelta)
        self.files.extend([file])

    def rmFile(self, indexes: Union[int, Iterable[int]]):
        if isinstance(indexes, int):
            indexes = (indexes,)
        del self.files[indexes]

    # def subList(self, filepath: List[str]): # need a tmp location in h5file
    #     ds = self.files.dataset
    #     path = ds['path']
    #     slt = np.zeros(len(ds), dtype=bool)
    #     for p in filepath:
    #         slt |= path == p

    #     raise NotImplementedError()
    #     # subList: FileList = FileList.create_at(HDF5.MemoryLocation(), 'tmp')
    #     subList.files.extend(ds[slt])

    def clear(self):
        self.files.clear()
        self.initialize()

    def __iter__(self):
        return iter(self.files)

    def __len__(self):
        return len(self.files)
