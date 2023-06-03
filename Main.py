# -*- coding: utf-8 -*-
# python 3.8
try:
    import os
    import sys
    import multiprocessing
    import argparse

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = '1'
    os.environ["OPENBLAS_NUM_THREADS"] = '1'
    os.environ["GOTO_NUM_THREADS"] = '1'
    os.environ["OMP_NUM_THREADS"] = '1'

    multiprocessing.set_start_method('spawn', True)

    if __name__ == "__main__":
        multiprocessing.freeze_support()

        # import pythoncom
        # pythoncom.CoInitialize()

        parser = argparse.ArgumentParser()
        parser.add_argument("workspacefile", nargs='?')
        parser.add_argument("--debug", action="store_true")
        parser.add_argument("--no_multiprocess", action="store_true")
        parser.add_argument("--to_step")

        from Orbitool.config import setting
        setting.save_setting()
        args = parser.parse_args()
        if args.debug:
            setting.debug.thread_block_gui = True
        if args.no_multiprocess:
            setting.debug.NO_MULTIPROCESS = True

        import matplotlib as mpl
        mpl.rcParams['agg.path.chunksize'] = 10000

        from PyQt5 import QtCore, QtWidgets
        # QtWidgets.QApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        app = QtWidgets.QApplication(sys.argv)
        app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))

        from Orbitool.UI import MainUiPy

        MainWin = MainUiPy.Window(args.workspacefile)
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

except Exception as e:
    import traceback
    import datetime
    with open("log.txt", 'a') as f:
        f.writelines([
            datetime.datetime.now().isoformat(),
            traceback.format_exc()])
    traceback.print_exc()
