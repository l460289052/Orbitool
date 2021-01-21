import os
from PyQt5 import QtWidgets
from functools import wraps
from types import FunctionType


def openfile(caption, filter=None, multi=False):
    assert not isinstance(caption, FunctionType)
    openfile_dir = '../.'

    def f(func):
        @wraps(func)
        def ff(self):

            kwargs = dict(caption=caption,
                          directory=openfile_dir, filter=filter)

            files, typ = QtWidgets.QFileDialog.getOpenFileNames(
                **kwargs) if multi else QtWidgets.QFileDialog.getOpenFileName(**kwargs)

            if not multi:
                files = [files]
            if len(files) == 0:
                return
            for f in files:
                assert os.path.isfile(f), "file not exist"
            return func(self, files if multi else files[0])
        return ff
    return f


def openfolder(caption):
    openfolder_dir = './..'

    def f(func):
        @wraps(func)
        def ff(self):

            folder, typ = QtWidgets.QFileDialog.getExistingDirectory(
                caption=caption, directory=openfolder_dir)

            if len(folder) == 0:
                return
            return func(self, folder)
        return ff
    return f
