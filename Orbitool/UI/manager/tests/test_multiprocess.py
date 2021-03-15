from typing import List, Tuple
from multiprocessing import Pool, freeze_support
from time import sleep

from PyQt5 import QtWidgets, QtCore
from .. import MultiProcess


class p(MultiProcess):
    @staticmethod
    def func(input):
        sleep(1)
        return input

    @staticmethod
    def read(file, args, i):
        sleep(0.1)
        return 123

    @staticmethod
    def write(file, args, i, ret):
        file["ret"][i] = ret

    @staticmethod
    def abort_finish(file, args):
        del file["ret"]

    @staticmethod
    def finish(file: dict, args):
        ret = file["ret"]
        file.clear()
        file.update(ret)

    @staticmethod
    def initialize(file, args):
        file["ret"] = {}


freeze_support()


def test_normal():
    app = QtWidgets.QApplication([])
    num = 20
    file = {i: i for i in range(num)}
    pp = p(file, {}, num, Pool(10))
    pp.start()
    pp.wait()
    # pp.run()

    assert file == {i: 123 for i in range(num)}


def test_abort():
    app = QtWidgets.QApplication([])
    num = 20
    file = {i: i for i in range(num)}
    pp = p(file, {}, num, Pool(10))

    pp.start()

    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.timeout.connect(loop.quit)
    timer.start(1)
    loop.exec_()
    timer.stop()

    pp.abort()

    pp.wait()

    assert file == {i: i for i in range(num)}
