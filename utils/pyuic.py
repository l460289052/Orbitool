from pathlib import Path
import os


def pyuic(path):
    path = Path(path)
    for ui in path.glob("**/*.ui"):
        uipy = ui.with_name(ui.stem + 'Ui.py')

        exist = os.path.exists(uipy)
        if not exist or os.path.getmtime(ui) > os.path.getmtime(uipy):
            if exist:
                print("Override old version", ui)
            else:
                print("Generate", ui)
            os.system(f'pyuic6 {ui} -o {uipy}')


def clear(path):
    path = Path(path)
    for ui in path.glob("**/*.ui"):
        uipy = ui.with_name(ui.stem + 'Ui.py')
        exist = os.path.exists(uipy)
        if exist:
            os.remove(uipy)
