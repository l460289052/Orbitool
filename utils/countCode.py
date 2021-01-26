import os
import shutil

from Orbitool.utils.files import FolderTraveler

exts = ['.py', '.pyx', '.pxd']


def iterator(*args):
    for i in args:
        for j in i:
            yield j


def count(recurrent_path, not_recurrent_path):
    cnt = 0
    size = .0
    fts = [FolderTraveler(not_recurrent_path, exts, False),
           FolderTraveler(recurrent_path, exts, True)]

    for file in iterator(*fts):
        if not file.lower().endswith('ui.py'):
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = [line for line in lines if len(line) > 5]

                fsize = os.path.getsize(file) / 1024
                size += fsize
                print(len(lines), format(fsize, '.4'), 'KB', file)
                cnt += len(lines)

    print('Total:', cnt, 'lines', format(size, '.4'), 'KB')
