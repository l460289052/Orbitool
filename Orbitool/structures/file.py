from typing import Dict, Tuple, Union, Iterable, List
from datetime import datetime

from sortedcontainers import SortedDict

from Orbitool.structures import HDF5
from Orbitool.utils.readers import ThermoFile


class File(HDF5.Group):
    h5_type = HDF5.RegisterType("File")
    path = HDF5.Str()
    creationDatatime = HDF5.Datetime()
    startTimedelta = HDF5.TimeDelta()
    endTimedelta = HDF5.TimeDelta()

    def initialize(self, path, creationDatatime, startTimedelta, endTimedelta):
        self.path = path
        self.creationDatatime = creationDatatime
        self.startTimedelta = startTimedelta
        self.endTimedelta = endTimedelta

    @property
    def startDatetime(self):
        return self.creationDatatime+self.startTimedelta

    @property
    def endDatetime(self):
        return self.creationDatatime+self.endTimedelta


class FileList(HDF5.Group):
    h5_type = HDF5.RegisterType("FileList")
    files: HDF5.Dict = HDF5.Dict.descriptor(File)

    def _crossed(self, start: datetime, end: datetime) -> Tuple[bool, File]:
        for file in self.files.values():
            file: File
            if start < file.endDatetime and file.startDatetime < end:
                return False, file
        return True, None

    def timeRange(self):
        if len(self.files) == 0:
            return None, None
        files = iter(self.files.values())
        f: File = next(files)
        s = f.startDatetime
        e = f.endDatetime
        for f in files:
            if f.startDatetime < s:
                s = f.startDatetime
            if f.endDatetime > e:
                e = f.endDatetime
        return s, e

    def addFile(self, filepath):
        f = ThermoFile(filepath)

        crossed, crossedFile = self._crossed(
            f.startDatetime, f.endDatetime)
        if crossed:
            raise ValueError('file "%s" and "%s" have crossed scan time' % (
                f.path, crossedFile.path))

        addf: File = self.files.additem(f.path)
        addf.initialize(addf.path, addf.creationDatatime,
                        addf.startTimedelta, addf.endTimedelta)

    def rmFile(self, filepath: Union[str, Iterable]):
        files = self.files
        if isinstance(filepath, str):
            filepath = [filepath]
        for p in filepath:
            del files[p]

    def subList(self, filepath: List[str]):
        subList = FileList.create_at(HDF5.MemoryLocation(), 'tmp')
        t_files: HDF5.Dict = subList.files
        files = self.files
        for p in filepath:
            t_f: File = t_files.additem(p)
            f = files[p]
            t_f.copy_from(f)

    def clear(self):
        self.files.clear()
        self.initialize()

    def keys(self):
        return self.files.keys()

    def values(self):
        return self.files.values()
