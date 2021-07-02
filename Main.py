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
    parser.add_argument("--to_step")

    from Orbitool import config
    args = parser.parse_args()
    config.DEBUG = args.debug

    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))

    from Orbitool.UI import MainUiPy

    if config.DEBUG:
        QtWidgets.QMessageBox.information(None, 'info', 'DEBUG')

    MainWin = MainUiPy.Window()
    MainWin.show()
    if args.to_step:
        steps = {
            "file": 0,
            "noise": 1,
            "peak-fit": 2,
            "calibration": 3
        }
        step = steps[args.to_step]
        from Orbitool.UI.tests import routine
        routine.init(MainWin)
        if step > 0:
            routine.fileui(MainWin)
            routine.file_spectra(MainWin)
        if step > 1:
            routine.noise(MainWin)
        if step > 2:
            routine.peak_shape(MainWin)
    sys.exit(app.exec_())
