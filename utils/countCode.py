import os
import shutil
from itertools import chain
from typing import TypedDict

from Orbitool.utils.files import FolderTraveler

exts = ['.py', '.pyx', '.pxd', '.pyi']


class File(TypedDict):
    lines: int
    size: float
    name: str


def count(recurrent_path, not_recurrent_path, count_blank_line=False):
    cnt = 0
    line_cnt = 0
    size = .0
    fts = [FolderTraveler(not_recurrent_path, exts, False),
           FolderTraveler(recurrent_path, exts, True)]

    files = []
    for file in chain.from_iterable(fts):
        if not file.lower().endswith('ui.py'):
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not count_blank_line:
                    lines = [line for line in lines if len(line) > 5]

                fsize = os.path.getsize(file) / 1024
                files.append(File(lines=len(lines), size=fsize, name=file))
                cnt += 1
                line_cnt += len(lines)
                size += fsize
    files.sort(key=lambda f: f['lines'], reverse=True)
    for f in files:
        print(f['lines'], format(f['size'], '.4'), 'KB', f['name'])

    print('Total:', cnt, "files",
          line_cnt, 'lines', format(size, '.4'), 'KB')
