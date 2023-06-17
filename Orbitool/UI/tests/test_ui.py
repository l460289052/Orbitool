import io
import logging
import os
from PyQt6 import QtWidgets, QtCore
import tempfile
# from pytestqt import qtbot
from ..MainUiPy import Window
from ...workspace import WorkSpace

from .routine import init, fileui, file_spectra, noise, qt_exit


# def test_precedure(qtbot: qtbot.QtBot):
def test_precedure():
    logger = logging.getLogger("Orbitool")
    with io.StringIO() as logs:
        handler = logging.StreamHandler(logs)
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)

        app = QtWidgets.QApplication([])
        window = Window()
        init(window)
        window.show()
        print("show window")
        fileui(window)
        print("finish test file tab")
        file_spectra(window)
        print("finish test file spectra")
        noise(window)
        print("finish test noise")
        print("ui test finished")

        window.close()        
        
        assert not logs.getvalue()


def test_export_load():
    with tempfile.TemporaryDirectory(prefix="orbitool_test") as tmpdir:
        tmppath = os.path.join(tmpdir, "tmp.Orbitool")

        app = QtWidgets.QApplication([])
        window = Window()

        window.manager.save.emit()
        window.manager.workspace.close_as(tmppath)
        window.manager.workspace = WorkSpace(tmppath)
        window.manager.init_or_restored.emit()
        window.close()
