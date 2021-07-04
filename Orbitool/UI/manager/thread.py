from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from multiprocessing import Pool
from multiprocessing.pool import AsyncResult
from queue import Queue
from typing import List, Tuple, final, Deque, Iterable, Generator, TypeVar, Generic, Any

from PyQt5 import QtCore

from ...config import logger, multi_cores
from ..utils import sleep


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
        self.result = None

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result = result
            self.finished.emit((result,))
        except Exception as e:
            self.finished.emit((e, ))

    def sendStatusFunc(self, *args):
        self.sendStatus.emit(*args)


Data = TypeVar("Data")
Result = TypeVar("Result")


class MultiProcess(QtCore.QThread, Generic[Data, Result]):
    finished = QtCore.pyqtSignal(tuple)
    sendStatus = QtCore.pyqtSignal(str, int, int)

    @final
    def __init__(self, file, read_kwargs: dict=None, func_kwargs:dict=None, write_kwargs:dict=None) -> None:
        super().__init__()
        self.file = file
        self.read_kwargs = read_kwargs or {}
        self.func_kwargs = func_kwargs or {}
        self.write_kwargs = write_kwargs or {}
        self.aborted = False

    @final
    def run(self):
        file = self.file
        results: Deque[AsyncResult] = deque()
        queue = Queue()

        def iter_queue():
            while True:
                result = queue.get()
                if result is None:
                    break
                yield result

        write_thread = Thread(self.write, (file, iter_queue()), self.write_kwargs)
        write_thread.start()
        limit_parallel = int(multi_cores * 1.3)
        with Pool(multi_cores) as pool:

            for i, input_data in enumerate(self.read(file, **self.read_kwargs)):
                if self.aborted:
                    queue.put(None)
                    return self.exception(file)
                results.append(pool.apply_async(
                    self.process, (i, self.func, input_data, self.func_kwargs)))
                if i >= limit_parallel:
                    ret = results.popleft()
                    while not ret.ready():
                        sleep(0.01)
                    ret = ret.get()
                    if isinstance(ret, Exception):
                        self.exception(file)
                        self.finished.emit(
                            (ret, (self.func, self.file, self.kwargs)))
                        queue.put(None)
                        return
                    queue.put(ret)

            while results:
                ret = results.popleft()
                while not ret.ready():
                    sleep(0.01)
                ret = ret.get()
                if isinstance(ret, Exception):
                    self.exception(file)
                    self.finished.emit(
                        (ret, (self.func, self.file)))
                    queue.put(None)
                    return
                queue.put(ret)

            queue.put(None)

        write_thread.wait()
        self.finished.emit((write_thread.result,))

    @final
    def abort(self, send=True):
        if send:
            self.finished.emit(
                (RuntimeError("Aborted"), (self.func, self.file, self.args)))
        self.aborted = True

    @final
    @staticmethod
    def process(label, func, data, kwargs):
        try:
            ret = func(data, **kwargs)
        except Exception as e:
            logger.error(str(e), exc_info=e)
            return e
        return ret

    @staticmethod
    def func(data: Data, **kwargs) -> Result:
        raise NotImplementedError()

    @staticmethod
    def read(file, **kwargs) -> Generator[Data, Any, Any]:
        raise NotImplementedError()
        # example
        for i in range(10):
            yield i

    @staticmethod
    def write(file, rets: Iterable[Result], **kwargs):
        raise NotImplementedError()
        # example
        for ret in rets:
            print(ret)
        return file

    @staticmethod
    def exception(file, **kwargs):
        raise NotImplementedError()
