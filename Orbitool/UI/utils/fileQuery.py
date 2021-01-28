import os
from PyQt5 import QtWidgets
from functools import wraps
from typing import Tuple, List

openfile_dir = '../.'
openfolder_dir = './..'


def openfile(caption, filter) -> Tuple[bool, str]:
    global openfile_dir
    f, typ = QtWidgets.QFileDialog.getOpenFileName(
        caption=caption, directory=openfile_dir, filter=filter)

    if len(f) == 0:
        return False, f
    assert os.path.isfile(f), "file not exist"

    openfile_dir = os.path.dirname(f)
    return True, f


def openfiles(caption, filter) -> List[str]:
    global openfile_dir
    f, typ = QtWidgets.QFileDialog.getOpenFileNames(
        caption=caption, directory=openfile_dir, filter=filter)

    if len(f) > 0:
        openfile_dir = os.path.dirname(f[0])
    return f


def openfolder(caption) -> Tuple[bool, str]:
    global openfolder_dir
    folder = QtWidgets.QFileDialog.getExistingDirectory(
        caption=caption, directory=openfolder_dir)

    if len(folder) == 0:
        return False, folder
    openfolder_dir = os.path.dirname(folder)
    return True, folder
