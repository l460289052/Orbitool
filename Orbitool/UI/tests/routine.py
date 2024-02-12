import os

from PyQt6 import QtWidgets, QtCore
from Orbitool import config, setting
from .. import MainUiPy
from .. import file_tab

from ..utils import test


loop: QtCore.QEventLoop = None


def wait_not_busy():
    if not setting.debug.DEBUG:
        loop.exec()
    sleep()


def sleep(timeout=None):
    if not timeout:
        timeout = setting.test_timeout
    if timeout > 0:
        timer = QtCore.QTimer()
        timer.timeout.connect(loop.quit)
        timer.start(timeout * 1000)
        loop.exec()


def wait(thread: QtCore.QThread):
    thread.finished.connect(loop.quit)
    loop.exec()


def init(window: MainUiPy.Window):
    global loop
    loop = QtCore.QEventLoop()
    window.manager.busy_signal.connect(loop.quit)


def qt_exit(app: QtWidgets.QApplication):
    timer = QtCore.QTimer()
    timer.timeout.connect(app.exit)
    timer.start(setting.test_timeout)


def fileui(window: MainUiPy.Window):
    fileui = window.fileTab
    manager = fileui.manager
    workspace = manager.workspace
    test.input(config.ROOT_PATH.parent / 'data')
    sleep()
    fileui.addFolder()

    wait_not_busy()
    assert not manager.busy
    assert workspace.file_tab.info.pathlist.paths

    test.input([1, 2, 3])
    fileui.processSelected()
    wait_not_busy()
    assert len(workspace.file_tab.info.spectrum_infos) > 0


def file_spectra(window: MainUiPy.Window):
    spectra = window.spectraList
    assert spectra.comboBox.currentIndex() == 0
    assert spectra.tableWidget.rowCount() > 0


def noise(window: MainUiPy.Window):
    window.tabWidget.setCurrentWidget(window.noiseTab)
    sleep()

    noiseui = window.noiseTab
    noiseui.showSelectedSpectrum()

    wait_not_busy()

    noiseui.calcNoise()

    wait_not_busy()
    noiseui.denoise()

    wait_not_busy()


def peak_shape(window: MainUiPy.Window):
    window.peakShapeTab.finishPeakShape()

# def calibration(window:MainUiPy.Window):
