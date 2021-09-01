from typing import List, Tuple
from multiprocessing import freeze_support
from time import sleep

from PyQt5 import QtWidgets, QtCore
from .. import MultiProcess, Manager
from .... import get_config


class p(MultiProcess):
    @staticmethod
    def func(input):
        return input

    @staticmethod
    def read(file, length):
        for i in range(length):
            yield i

    @staticmethod
    def read_len(file, length) -> int:
        return length

    @staticmethod
    def write(file, rets):
        target = []
        file["ret"] = target
        cnt = 0
        for ret in rets:
            target.append(ret)
            cnt += 1
        return cnt

    @staticmethod
    def exception(file, args):
        del file["ret"]


# freeze_support()


# def test_normal():
#     app = QtWidgets.QApplication([])
#     num = 20
#     file = {}
#     pp = p(file, {"length": 20})
#     # pp.start()
#     # pp.wait()
#     pp.run()
#     if isinstance(pp.result[0], Exception):
#         raise pp.result[0]

#     assert file == {"ret": list(range(20))}

def test_single():
    config = get_config()
    # config.DEBUG = True
    config.NO_MULTIPROCESS = True
    app = QtWidgets.QApplication([])
    num = 20
    file = {}
    pp = p(file, {"length": 20})
    pp.start()
    pp.wait()
    # pp.run()
    if isinstance(pp.result[0], Exception):
        raise pp.result[0]

    assert file == {"ret": list(range(20))}


# def test_abort():
#     app = QtWidgets.QApplication([])
#     num = 20
#     file = {}
#     pp = p(file, {"length": 20})

#     pp.start()

#     loop = QtCore.QEventLoop()
#     timer = QtCore.QTimer()
#     timer.timeout.connect(loop.quit)
#     timer.start(1)
#     loop.exec_()
#     timer.stop()

#     pp.abort()

#     pp.wait()

#     assert file == {}
