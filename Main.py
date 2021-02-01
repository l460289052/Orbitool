# -*- coding: utf-8 -*-
import sys
import multiprocessing
import argparse


multiprocessing.set_start_method('spawn', True)

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # import pythoncom
    # pythoncom.CoInitialize()

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")

    from Orbitool import config
    args = parser.parse_args()
    config.DEBUG = args.debug

    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))

    from Orbitool.UI import MainUiPy

    MainWin = MainUiPy.Window()
    MainWin.show()
    sys.exit(app.exec_())
