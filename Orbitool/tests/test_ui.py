import os
from PyQt5 import QtCore
from time import sleep

from pytestqt import qtbot
from Orbitool.UI import MainUiPy, FileUiPy
from Orbitool.UI import utils as UiUtils
from Orbitool.UI import manager

from Orbitool import config

from queue import Queue

queue = Queue()


def pipe(*args, **kwargs):
    return queue.get()


UiUtils.openfile = pipe
UiUtils.openfiles = pipe
UiUtils.openfolder = pipe


def wait_not_busy(widget: manager.BaseWidget, timeout_second=None):
    while widget.busy.get():
        sleep(0.1)
        if timeout_second is not None:
            timeout_second -= 0.1
            if timeout_second < 0:
                break


def test_precedure(qtbot: qtbot.QtBot):
    window = MainUiPy.Window()
    window.show()

    qtbot.addWidget(window)

    fileui(qtbot, window.fileUi)


def fileui(qtbot, fileui: FileUiPy.Widget):
    queue.put((True, os.path.join(os.path.dirname(config.rootPath), 'data')))
    qtbot.mouseClick(fileui.addFolderPushButton, QtCore.Qt.LeftButton)

    qtbot.waitSignal(fileui.node_thread.finished)
    assert len(fileui.workspace.file_list) == 4
    assert fileui.tableWidget.rowCount() == 4
