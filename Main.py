import sys
import multiprocessing


multiprocessing.set_start_method('spawn', True)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # import pythoncom
    # pythoncom.CoInitialize()

    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)

    import OribitoolUiPy

    MainWin = OribitoolUiPy.Window()
    MainWin.show()
    sys.exit(app.exec_())
