import os


def pyuic(path):
    for ui in os.listdir(path):
        if os.path.splitext(ui)[1].lower() == '.ui':
            ui = os.path.join(path, ui)
            uipy = os.path.splitext(ui)[0] + 'Ui.py'
            exist = os.path.exists(uipy)
            if not exist or os.path.getmtime(ui) > os.path.getmtime(uipy):
                if exist:
                    print("Override old version", ui)
                else:
                    print("Generate", ui)
                os.system(f'pyuic5 {ui} -o {uipy}')


def clear(path):
    for ui in os.listdir(path):
        if os.path.splitext(ui)[1].lower() == '.ui':
            ui = os.path.join(path, ui)
            uipy = os.path.splitext(ui)[0] + 'Ui.py'
            exist = os.path.exists(uipy)
            if exist:
                os.remove(uipy)
