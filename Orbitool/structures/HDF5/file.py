from __future__ import annotations
import os
import tempfile
from datetime import datetime

import h5py

from . import h5obj
from . import descriptor

from ... import config


class File(h5obj.H5Obj):
    h5_type = descriptor.RegisterType('File')

    def __init__(self, path, inited=True):
        if path is None:
            assert not inited, f"You should call {self.h5_type.type_name}.create_at instead of {self.h5_type.type_name}.__init__"
            self.tempDir = tempfile.TemporaryDirectory(
                prefix=datetime.now().strftime(config.TempFile.prefixTimeFormat), dir=config.TempFile.tempPath)
            self.location = h5py.File(os.path.join(
                self.tempDir.name, 'tmp.hdf5'), 'a')
        else:
            self.tempDir = None
            self.location = h5py.File(path, 'a')
            assert not inited or self.h5_type.attr_type_name == self.h5_type.type_name

    @classmethod
    def create_at(cls, path) -> File:
        obj = cls(path, False)
        for desc in cls._export_value_names[obj.h5_type.type_name].values():
            desc.on_create(obj)
        return obj

    @classmethod
    def openOrCreateInitialize(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def descriptor(cls, name):
        raise NotImplementedError()

    def __del__(self):
        self.location.close()