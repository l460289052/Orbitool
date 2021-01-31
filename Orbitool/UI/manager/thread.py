from enum import Enum
from PyQt5 import QtCore


class threadtype(Enum):
    thread = 0
    multiprocess = 1


class Thread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, int, int)

    def __init__(self, func, args = (), kwargs = {}) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit((result, (self.func, self.args, self.kwargs)))
        except Exception as e:
            self.finished.emit((e, (self.func, self.args, self.kwargs)))

    def sendStatusFunc(self, *args):
        self.sendStatus.emit(*args)


class MultiProcess(QtCore.QThread):
    """
    should be abortable
    """
    pass
