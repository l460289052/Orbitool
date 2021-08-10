import os
from itertools import chain
from Orbitool.utils.files import FolderTraveler


def collect(root_path, recurrent_path, not_recurrent_path):
    exts = ['.py', '.pyx', '.pxd', '.pyi']
    begin_splitter = "*" * 40
    end_splitter = "*" * 80

    fts = [FolderTraveler(not_recurrent_path, exts, False),
           FolderTraveler(recurrent_path, exts, True)]

    for file in chain.from_iterable(fts):
        if file.lower().endswith("ui.py"):
            continue
        print(str(os.path.relpath(file, root_path)))
        print(begin_splitter)
        with open(file, 'r', encoding='utf-8') as reader:
            lines = reader.readlines()
            lines = [line.strip("\n") for line in lines]
            list(map(print, lines))
            print(end_splitter)
            print()
