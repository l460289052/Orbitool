import os
import shutil

from .files import FolderTraveler

recurrent = os.path.dirname(os.path.dirname(__file__))
notRecurrent = os.path.dirname(recurrent)

exts = ['.py','.pyx','.pxd']

def iterator(*args):
    for i in args:
        for j in i:
            yield j

def main():
    cnt = 0
    fts = [FolderTraveler(notRecurrent, exts, False), FolderTraveler(recurrent, exts, True)]

    for file in iterator(*fts):
        if not file.lower().endswith('ui.py'):
            with open(file,'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = [line for line in lines if len(line) > 5]

                print(len(lines), file)
                cnt += len(lines)

    print('Total:', cnt)


if __name__ == "__main__":
    main()