from PyQt5 import QtWidgets, QtCore
from .. import MainUiPy

from .routine import init, fileui, file_spectra, noise


def test_precedure():
    app = QtWidgets.QApplication([])
    window = MainUiPy.Window()

    init(window)
    window.show()
    fileui(window)
    file_spectra(window)
    noise(window)

    window.close()

