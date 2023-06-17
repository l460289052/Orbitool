# -*- coding: utf-8 -*-
# python 3.11
try:
    import os
    import multiprocessing

    multiprocessing.set_start_method('spawn', True)

    if __name__ == "__main__":
        multiprocessing.freeze_support()

        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = '1'
        # os.environ["QT_SCALE_FACTOR"] = "1"

        # import pythoncom
        # pythoncom.CoInitialize()

        import argparse
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
        mpl.use("QtAgg")
        mpl.rcParams['agg.path.chunksize'] = 10000

        from PyQt6 import QtCore, QtWidgets, QtGui

        import sys
        app = QtWidgets.QApplication(sys.argv)
        style = QtWidgets.QStyleFactory.create('Fusion')
        app.setStyle(style)

        setting.set_global_var("app", app)

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
        sys.exit(app.exec())

except Exception as e:
    import traceback
    import datetime
    with open("log.txt", 'a') as f:
        f.writelines([
            datetime.datetime.now().isoformat(),
            traceback.format_exc()])
    traceback.print_exc()
