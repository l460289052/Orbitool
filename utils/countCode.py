import os
import shutil

from Orbitool.utils.files import FolderTraveler

exts = ['.py','.pyx','.pxd']

def iterator(*args):
    for i in args:
        for j in i:
            yield j

def count(recurrent_path, not_recurrent_path):
    cnt = 0
    fts = [FolderTraveler(not_recurrent_path, exts, False), FolderTraveler(recurrent_path, exts, True)]

    for file in iterator(*fts):
        if not file.lower().endswith('ui.py'):
            with open(file,'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = [line for line in lines if len(line) > 5]

                print(len(lines), file)
                cnt += len(lines)

    print('Total:', cnt)