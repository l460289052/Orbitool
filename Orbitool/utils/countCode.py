import os
import shutil

from files import FolderTraveler

notRecurrent = ".."
recurrent = ['../utils', '../tests', '../functions']

exts = ['.py','.pyx','.pxd']

def iterator(*args):
    for i in args:
        for j in i:
            yield j

def main():
    cnt = 0
    fts = [FolderTraveler(notRecurrent, exts, False), FolderTraveler(recurrent, exts, True)]

    for file in iterator(*fts):
        if 'Ui.Py' not in file:
            with open(file,'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = [line for line in lines if len(line) > 5]

                print(len(lines), file)
                cnt += len(lines)

    print('Total:', cnt)


if __name__ == "__main__":
    main()