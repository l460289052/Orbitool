import os
import tempfile
import shutil


def clear():
    tempdir = tempfile.gettempdir()

    for path in os.listdir(tempdir):
        if path.startswith("orbitool"):
            path = os.path.join(tempdir, path)
            print(f"remove {path}")
            shutil.rmtree(path)