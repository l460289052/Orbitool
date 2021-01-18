import os


def main():
    dirpath = "Orbitool/UI"
    for ui in os.listdir(dirpath):
        if os.path.splitext(ui)[1].lower() == '.ui':
            ui = os.path.join(dirpath, ui)
            uipy = os.path.splitext(ui)[0]+'Ui.py'
            exist = os.path.exists(uipy)
            if not exist or os.path.getmtime(ui) > os.path.getmtime(uipy):
                if exist:
                    print("Override old version", ui)
                else:
                    print("Generate", ui)
                os.system(f'pyuic5 {ui} -o {uipy}')


if __name__ == "__main__":
    main()
