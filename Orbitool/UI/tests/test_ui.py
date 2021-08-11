import os
from PyQt5 import QtWidgets, QtCore
import tempfile
from .. import MainUiPy
from ...workspace import WorkSpace

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


def test_export_load():
    with tempfile.TemporaryDirectory(prefix="orbitool_test") as tmpdir:
        tmppath = os.path.join(tmpdir, "tmp.Orbitool")

        app = QtWidgets.QApplication([])
        window = MainUiPy.Window()

        window.manager.save.emit()
        window.manager.workspace.close_as(tmppath)
        window.manager.workspace = WorkSpace(tmppath)
        window.manager.inited_or_restored.emit()
        window.close()
