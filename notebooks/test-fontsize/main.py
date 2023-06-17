import os
# os.environ["QT_FONT_DPI"] = "96"
# os.environ["QT_SCALE_FACTOR"] = "1.75"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = '1'
from mainUi import Ui_MainWindow
from PyQt6 import QtCore, QtWidgets, QtGui

class Window(QtWidgets.QMainWindow):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

if __name__ == "__main__":
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QtWidgets.QApplication([])
    screen = app.screens()[0]
    print(screen.devicePixelRatio(), screen.physicalSize(), screen.logicalDotsPerInch())

    win = Window()
    win.show()

    app.exec()