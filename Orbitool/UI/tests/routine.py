import os

from PyQt5 import QtWidgets, QtCore
from ... import config
from .. import MainUiPy, FileUiPy

from ..utils import test


loop: QtCore.QEventLoop = None


def wait_not_busy():
    if not config.DEBUG:
        loop.exec_()


def sleep(timeout=None):
    if not timeout:
        timeout = config.test_timeout
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
    assert len(workspace.info.filelist.files) == 4

    test.input([1, 2, 3])
    fileui.processSelected()
    wait_not_busy()
    sleep()
    assert len(workspace.spectra_list.info.file_spectrum_info_list) > 0


def file_spectra(window: MainUiPy.Window):
    spectra = window.spectraList
    assert spectra.comboBox.currentIndex() == 0
    assert spectra.tableWidget.rowCount() > 0


def noise(window: MainUiPy.Window):
    window.tabWidget.setCurrentWidget(window.noiseTab)

    noiseui = window.noiseTab
    noiseui.showSelectedSpectrum()

    wait_not_busy()
    sleep()

    noiseui.calcNoise()
    noiseui.denoise()
