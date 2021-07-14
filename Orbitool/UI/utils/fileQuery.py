import os
from PyQt5 import QtWidgets
from functools import wraps
from typing import Tuple, List

from . import test

savefile_dir = '../.'
openfile_dir = '../.'
openfolder_dir = './..'


@test.override_input
def savefile(caption, filter, prefer_name=None) -> Tuple[bool, str]:
    global savefile_dir
    if prefer_name:
        path = os.path.join(savefile_dir, prefer_name)
    else:
        path = savefile_dir
    f, typ = QtWidgets.QFileDialog.getSaveFileName(
        caption=caption, directory=path, filter=filter)

    if len(f) == 0:
        return False, f
    savefile_dir = os.path.dirname(f)
    return True, f


@test.override_input
def openfile(caption, filter) -> Tuple[bool, str]:
    global openfile_dir
    f, typ = QtWidgets.QFileDialog.getOpenFileName(
        caption=caption, directory=openfile_dir, filter=filter)

    if len(f) == 0:
        return False, f
    assert os.path.isfile(f), "file not exist"

    openfile_dir = os.path.dirname(f)
    return True, f


@test.override_input
def openfiles(caption, filter) -> List[str]:
    global openfile_dir
    f, typ = QtWidgets.QFileDialog.getOpenFileNames(
        caption=caption, directory=openfile_dir, filter=filter)

    if len(f) > 0:
        openfile_dir = os.path.dirname(f[0])
    return f


@test.override_input
def openfolder(caption) -> Tuple[bool, str]:
    global openfolder_dir
    folder = QtWidgets.QFileDialog.getExistingDirectory(
        caption=caption, directory=openfolder_dir)

    if len(folder) == 0:
        return False, folder
    openfolder_dir = os.path.dirname(folder)
    return True, folder
