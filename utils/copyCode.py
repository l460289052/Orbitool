import os
import shutil
from itertools import chain

from Orbitool.utils.files import FolderTraveler

def copyTo(root):
    root = os.path.abspath(root)
    codeexport = os.path.join(os.path.split(root)[0], 'codeexport')

    dsts = [
        "D:/Orbitool",
        codeexport ]

    shutil.rmtree(codeexport)
    os.mkdir(codeexport)

    notRecurrent = root
    recurrent = ['Orbitool', 'utils']
    recurrent = [os.path.join(root, r) for r in recurrent]

    exts = [".py", ".pyx", ".pxd", ".pyd", ".dll", ".md", ".yaml"]

    def checkBuildFolder(path):
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            checkBuildFolder(folder)
            os.mkdir(folder)

    def copyFileTo(file, dst):
        checkBuildFolder(dst)
        if not os.path.isfile(dst) or os.path.getmtime(file) > os.path.getmtime(dst):
            shutil.copyfile(file,dst)

    def copyTo(folder):
        ftNot = FolderTraveler(notRecurrent, exts, False)
        ftRec = FolderTraveler(recurrent, exts, True)
        for file in chain(ftNot, ftRec):
            file = os.path.relpath(file, root)
            copyFileTo(file, os.path.join(folder,file))

    for dst in dsts:
        copyTo(dst)
    
