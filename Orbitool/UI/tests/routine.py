import os

from PyQt5 import QtWidgets, QtCore
from ... import get_config, config
from .. import MainUiPy, FileUiPy

from ..utils import test


loop: QtCore.QEventLoop = None


def wait_not_busy():
    if not get_config().DEBUG:
        loop.exec_()


def sleep(timeout=None):
    if not timeout:
        timeout = get_config().test_timeout
    if timeout > 0:
        timer = QtCore.QTimer()
        timer.timeout.connect(loop.quit)
        timer.start(timeout * 1000)
        loop.exec_()


def wait(thread: QtCore.QThread):
    thread.finished.connect(loop.quit)
    loop.exec_()


def init(window: MainUiPy.Window):
    global loop
    loop = QtCore.QEventLoop()
    window.manager.busy_signal.connect(loop.quit)


def fileui(window: MainUiPy.Window):
    fileui = window.fileTab
    manager = fileui.manager
    workspace = manager.workspace
    test.input((True, os.path.join(os.path.dirname(config.rootPath), 'data')))
    sleep()
    fileui.addFolder()

    wait_not_busy()
    sleep()
    assert not manager.busy
    assert len(workspace.file_tab.info.pathlist.paths) == 9

    test.input([1, 2, 3])
    fileui.processSelected()
    wait_not_busy()
    sleep()
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
    sleep()

    noiseui.calcNoise()

    sleep()
    noiseui.denoise()

    sleep()


def peak_shape(window: MainUiPy.Window):
    window.peakShapeTab.finishPeakShape()

# def calibration(window:MainUiPy.Window):
