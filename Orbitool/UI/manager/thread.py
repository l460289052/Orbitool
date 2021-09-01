import logging
import os
from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from multiprocessing import Pool
from multiprocessing.pool import AsyncResult
from queue import Queue
from typing import (Any, Deque, Generator, Generic, Iterable, List, Tuple,
                    TypeVar, final)

from PyQt5 import QtCore

from ... import get_config
from ..utils import sleep
from . import manager

logger = logging.getLogger("Orbitool")


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

    def set_tqdmer(self, tqdmer: manager.TQDMER):
        pass


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
        self.tqdm: manager.TQDMER = None
        self.result = None

    @final
    def finished_emit(self, t: tuple):
        self.result = t
        self.finished.emit(t)

    @final
    def set_tqdmer(self, tqdmer: manager.TQDMER):
        self.tqdm = tqdmer

    @final
    def run(self):
        try:
            if self.tqdm is None:
                self.tqdm = manager.TQDMER()
            if get_config().NO_MULTIPROCESS:
                self._single_run_memory()
            else:
                self._run()
        except Exception as e:
            self.finished_emit((e,))

    @final
    def _run(self):
        file = self.file
        results: Deque[AsyncResult] = deque()
        queue = Queue()
        length = self.read_len(file, **self.read_kwargs)

        def iter_queue():
            tqdm = self.tqdm(msg="write", length=length)
            while True:
                tqdm.update()
                result = queue.get()
                if result is None:
                    break
                yield result

        write_thread = Thread(
            self.write, (file, iter_queue()), self.write_kwargs)
        write_thread.start()

        multi_cores = get_config().multi_cores

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
                        return
                while len(results) > 0 and results[0].ready():
                    ret = results.popleft().get()
                    if isinstance(ret, Exception):
                        self.finished_emit(
                            (ret, (self.func, self.file)))
                        self.abort()
                        return
                    queue.put(ret)

            for i, input_data in self.tqdm(
                    enumerate(self.read(file, **self.read_kwargs)),
                    length=length, msg="read",
                    immediate=True):

                if self.aborted:
                    return abort()
                results.append(pool.apply_async(
                    self.process, (i, self.func, input_data, self.func_kwargs)))
                wait_to_ready(False)

            while results:
                if self.aborted:
                    return abort()
                wait_to_ready(True)

            queue.put(None)

        write_thread.wait()
        self.finished_emit((write_thread.result,))

    @final
    def _single_run_memory(self):
        file = self.file

        def read_process():
            for i, data in enumerate(self.tqdm(self.read(file, **self.read_kwargs), "process")):
                yield self.process(i, self.func, data, self.func_kwargs)
        ret = self.write(file, read_process(), **self.write_kwargs)
        self.finished_emit((ret,))

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
