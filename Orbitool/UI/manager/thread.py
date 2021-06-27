from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from multiprocessing.pool import Pool as PoolType, AsyncResult
from queue import Queue
from typing import List, Tuple, final, Deque, Iterable

from PyQt5 import QtCore

from ...config import logger, multi_cores


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
            self.finished.emit((result,))
        except Exception as e:
            self.finished.emit((e, ))

    def sendStatusFunc(self, *args):
        self.sendStatus.emit(*args)


class MultiProcess(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, int, int)

    @final
    def __init__(self, file, args: dict, num: int, pool: PoolType = None) -> None:
        super().__init__()
        self.file = file
        self.args = args
        self.num = num
        self.pool = pool
        self.aborted = False

    @final
    def run(self):
        length = self.num
        results: Deque[AsyncResult] = deque()
        pool: PoolType = self.pool
        file = self.file
        args = self.args
        queue = Queue()

        def iter_queue():
            while True:
                result = queue.get()
                if result is None:
                    break
                yield result

        write_thread = Thread(self.write, (file, args, iter_queue()))
        write_thread.start()

        for i, input_data in enumerate(self.read(file, args)):
            if self.aborted:
                queue.put(None)
                return self.exception(file, args)
            results.append(pool.apply_async(
                self.process, (i, self.func, input_data)))
            if i >= multi_cores:
                ret = results.popleft().get()
                if isinstance(ret, Exception):
                    self.exception(file, args)
                    self.finished.emit(
                        (ret, (self.func, self.file, self.args)))
                    queue.put(None)
                    return
                queue.put(ret)

        while results:
            ret = results.popleft().get()
            if isinstance(ret, Exception):
                self.exception(file, args)
                self.finished.emit(
                    (ret, (self.func, self.file, self.args)))
                queue.put(None)
                return
            queue.put(ret)

        queue.put(None)

        write_thread.wait()

        self.finished.emit((True, (self.file, self.args)))

    @final
    def abort(self, send=True):
        if send:
            self.finished.emit(
                (RuntimeError("Aborted"), (self.func, self.file, self.args)))
        self.aborted = True

    @final
    @staticmethod
    def process(label, func, args):
        try:
            ret = func(args)
        except Exception as e:
            logger.error(str(e), exc_info=e)
            return e
        return ret

    @staticmethod
    def func(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def read(file, args):
        raise NotImplementedError()

    @staticmethod
    def write(file, args, rets: Iterable):
        raise NotImplementedError()

    @staticmethod
    def exception(file, args):
        raise NotImplementedError()
