from typing import List, Tuple
from multiprocessing import freeze_support
from time import sleep

from PyQt5 import QtWidgets, QtCore
from .. import MultiProcess


class p(MultiProcess):
    @staticmethod
    def func(input, *args, **kwargs):
        sleep(1)
        return input

    @staticmethod
    def read(file, args, kwargs):
        for i in range(args[0]):
            yield i

    @staticmethod
    def write(file, args, rets):
        target = []
        file["ret"] = target
        for ret in rets:
            target.append(ret)

    @staticmethod
    def exception(file, args):
        del file["ret"]


freeze_support()


def test_normal():
    app = QtWidgets.QApplication([])
    num = 20
    file = {}
    pp = p(file, [20], {})
    pp.start()
    pp.wait()
    # pp.run()

    assert file == {"ret": list(range(20))}


def test_abort():
    app = QtWidgets.QApplication([])
    num = 20
    file = {}
    pp = p(file, [20], {})

    pp.start()

    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.timeout.connect(loop.quit)
    timer.start(1)
    loop.exec_()
    timer.stop()

    pp.abort()

    pp.wait()

    assert file == {}
