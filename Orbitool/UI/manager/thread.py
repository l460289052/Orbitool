from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from multiprocessing import Pool
from multiprocessing.pool import AsyncResult
import os
from queue import Queue
from typing import List, Tuple, final, Deque, Iterable, Generator, TypeVar, Generic, Any

from PyQt5 import QtCore

from ...config import logger, multi_cores
from ..utils import sleep
from . import manager


class threadtype(Enum):
    thread = 0
    multiprocess = 1


class Thread(QtCore.QThread):
    finished = QtCore.pyqtSignal(tuple)

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
            self.result = e
            self.finished.emit((e, ))


Data = TypeVar("Data")
Result = TypeVar("Result")


class MultiProcess(QtCore.QThread, Generic[Data, Result]):
    finished = QtCore.pyqtSignal(tuple)

    @final
    def __init__(self, file, read_kwargs: dict = None, func_kwargs: dict = None, write_kwargs: dict = None) -> None:
        super().__init__()
        self.file = file
        self.read_kwargs = read_kwargs or {}
        self.func_kwargs = func_kwargs or {}
        self.write_kwargs = write_kwargs or {}
        self.aborted = False
        self.manager: manager.Manager = None

    @final
    def run(self):
        try:
            file = self.file
            results: Deque[AsyncResult] = deque()
            queue = Queue()
            length = self.read_len(file, **self.read_kwargs)

            def iter_queue():
                tqdm = self.manager.tqdm(msg="write", length=length)
                while True:
                    tqdm.update()
                    result = queue.get()
                    if result is None:
                        break
                    yield result

            write_thread = Thread(
                self.write, (file, iter_queue()), self.write_kwargs)
            write_thread.start()

            with Pool(multi_cores) as pool:
                def abort():
                    queue.put(None)
                    pool.terminate()
                    self.exception(file)

                def wait_to_ready(force: bool):
                    if len(results) == 0:
                        return
                    ret = results[0]
                    while not ret.ready():
                        if not force:
                            not_ready_num = len(
                                [r for r in results if not r.ready()])
                            # could put more task
                            if not_ready_num < multi_cores and len(results) < 2.5 * multi_cores:
                                return
                        sleep(.1)
                        if self.aborted:
                            return abort()
                    while len(results) > 0 and results[0].ready():
                        ret = results.popleft().get()
                        if isinstance(ret, Exception):
                            self.finished.emit(
                                (ret, (self.func, self.file)))
                            return abort()
                        queue.put(ret)

                for i, input_data in self.manager.tqdm(
                        enumerate(self.read(file, **self.read_kwargs)),
                        length=length, msg="read",
                        immediate=True):

                    if self.aborted:
                        return abort()
                    results.append(pool.apply_async(
                        self.process, (i, self.func, input_data, self.func_kwargs)))
                    wait_to_ready(False)

                while results:
                    wait_to_ready(True)

                queue.put(None)

            write_thread.wait()
            self.finished.emit((write_thread.result,))
        except Exception as e:
            self.finished.emit((e,))

    @final
    def abort(self, send=True):
        if send:
            self.finished.emit(
                (RuntimeError("Aborted"), (self.func, self.file)))
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
    def read_len(file, **read_kwargs) -> int:
        return -1

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
