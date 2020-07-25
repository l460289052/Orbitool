import os
from typing import Union, List


class FolderTraveler:
    """
    ft = FolderTraveler(".", true)
    for path in ft:
        print(path)
    """

    def __init__(self, rootPath: Union[str, List[str]], ext: Union[str, List[str]], recurrent: bool):
        if isinstance(rootPath, str):
            rootPaths = [rootPath]
        else:
            rootPaths = rootPath
        if isinstance(ext, str):
            exts = [ext]
        else:
            exts = ext
        for ext in exts:
            assert ext[0] == '.'
        exts = [ext.lower() for ext in exts]
        for path in rootPaths:
            assert os.path.isdir(path)
        self.roots = rootPaths
        self.exts = set(exts)
        self.recurrent = recurrent

    def _findFile(self, folder: str):
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if not os.path.isdir(path) and os.path.splitext(f)[1].lower() in self.exts:
                yield path

    def _findFileRecurrent(self, folder: str):
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isdir(path):
                for file in self._findFileRecurrent(path):
                    yield file
            elif os.path.splitext(f)[1].lower() in self.exts:
                yield path

    def __iter__(self):
        func = self._findFileRecurrent if self.recurrent else self._findFile
        for root in self.roots:
            for path in func(root):
                yield path
