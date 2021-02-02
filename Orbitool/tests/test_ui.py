import os
from PyQt5 import QtCore
from time import sleep

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


def test_precedure():
    window = MainUiPy.Window()
    window.show()

    fileui(window.fileUi)


def fileui(fileui: FileUiPy.Widget):
    queue.put((True, os.path.join(os.path.dirname(config.rootPath), 'data')))
    fileui.addFolder()

    fileui.node_thread.wait()
    assert len(fileui.current_workspace.file_list) == 4
    
    fileui.tableWidget.selectRow(1)
    fileui.tableWidget.selectRow(2)
    fileui.tableWidget.selectRow(3)
    fileui.show()
    
    sleep(1)

