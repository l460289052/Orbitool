import os
import shutil

from files import FolderTraveler

root = os.path.abspath(__file__)
while os.path.split(root)[1] != 'code':
    root = os.path.split(root)[0]

codeexport = os.path.join(os.path.split(root)[0], 'codeexport')

dsts = [
    "C:/CODE/Python/Orbitool",
    codeexport ]

shutil.rmtree(codeexport)
os.mkdir(codeexport)

notRecurrent = root
recurrent = ['utils', 'functions']
recurrent = [os.path.join(root, r) for r in recurrent]

exts = [".py", ".pyx", ".pxd", ".pyd", ".dll", ".md"]

def iterator(*args):
    for i in args:
        for j in i:
            yield j

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
    for file in iterator(ftNot, ftRec):
        file = os.path.relpath(file, root)
        copyFileTo(file, os.path.join(folder,file))

if __name__ == "__main__":
    for dst in dsts:
        copyTo(dst)
    
