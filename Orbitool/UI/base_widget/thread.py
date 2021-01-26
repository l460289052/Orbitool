from enum import Enum
from PyQt5 import QtCore


class threadtype(Enum):
    thread = 0
    multiprocess = 1


class Thread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, int, int)

    def __init__(self, args) -> None:
        super().__init__()
        self.func = args[0]
        self.args = args[1] if len(args) > 1 else tuple()
        self.kwargs = args[2] if len(args) > 2 else {}

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
