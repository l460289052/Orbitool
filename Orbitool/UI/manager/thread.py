from enum import Enum
from PyQt5 import QtCore
from abc import ABC, abstractmethod
from typing import List, Tuple
from multiprocessing import Manager, Pool, Queue
from typing import final

from ...config import multi_cores, logger


class threadtype(Enum):
    thread = 0
    multiprocess = 1


class Thread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, int, int)

    def __init__(self, func, args=(), kwargs={}) -> None:
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
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, int, int)

    @final
    def __init__(self, file, args: dict, num: int, pool: Pool = None) -> None:
        super().__init__()
        self.file = file
        self.args = args
        self.num = num
        self.pool = pool
        self.aborted = False

    @final
    def run(self):
        length = self.num
        results = []
        pool = self.pool
        file = self.file
        args = self.args
        self.initialize(file, args)
        manager = Manager()
        queue = manager.Queue()
        for i in range(length + multi_cores):
            if self.aborted:
                return self.abort_finish(file, args)
            if i < length:
                results.append(pool.apply_async(
                    self.process, (i, self.func, self.read(file, args, i), queue)))
            if i >= multi_cores:
                if (label := queue.get()) > 0:
                    ret = results[label].get()
                    self.write(file, args, label, ret)
                else:
                    self.abort(False)
                    self.finished.emit((RuntimeError(
                        "There are some wrongs in running, please check log.txt for more details"), (self.file, self.args)))

        self.finish(file, args)
        self.finished.emit((True, (self.file, self.args)))

    @final
    def abort(self, send=True):
        if send:
            self.finished.emit(
                (RuntimeError("Aborted"), (self.func, self.file, self.args)))
        self.aborted = True

    @final
    @staticmethod
    def process(label, func, args, queue: Queue):
        try:
            ret = func(args)
            queue.put(label)
        except Exception as e:
            logger.error(str(e), exc_info=e)
            queue.put(-label - 1)
        return ret

    @staticmethod
    def func(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def read(file, args, i):
        raise NotImplementedError()

    @staticmethod
    def write(file, args, i, ret):
        raise NotImplementedError()

    @staticmethod
    def abort_finish(file, args):
        raise NotImplementedError()

    @staticmethod
    def finish(file, args):
        raise NotImplementedError()

    @staticmethod
    def initialize(file, args):
        pass
