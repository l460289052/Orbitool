from __future__ import annotations
from functools import wraps
from datetime import datetime
from typing import Callable, Dict, Iterable, overload, TypeVar, Generic, Iterator, Type
import random


from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QTableWidget, QMainWindow
import numpy as np

from ...workspace import WorkSpace
from ..utils import showInfo
from ..component import Plot


class BindData:
    def __init__(self) -> None:
        self.peak_fit_left_index = DataBindSignal(int)


class Values:
    def __init__(self) -> None:
        self.calibration_info_selected_index = ValueGetter(int)
        self.mass_list_selected_indexes = ValueGetter(np.ndarray)
        self.spectra_list_selected_index = ValueGetter(int)


class Manager(QObject):
    """
    storage common resources
    """
    inited_or_restored = pyqtSignal()
    save = pyqtSignal()
    busy_signal = pyqtSignal(bool)
    msg = pyqtSignal(str)
    tqdm_signal = pyqtSignal(int, int, str)  # label, percent, msg

    def __init__(self) -> None:
        super().__init__()
        self.running_thread: QThread = None
        self.workspace: WorkSpace = None
        self._busy: bool = True
        self.progress_cnt = 0

        self.calibrationInfoWidget: QTableWidget = None
        self.formulas_result_win: QMainWindow = None

        self.bind = BindData()
        self.getters = Values()

    @overload
    def tqdm(self, iter: Iterable[T], msg: str = "") -> TQDM[T]:
        pass

    @overload
    def tqdm(self, iter: Iterable[T], msg: str = "", *, length: int = 0, immediate=False) -> TQDM[T]:
        pass

    @overload
    def tqdm(self, *, msg: str = "", length: int = 0) -> TQDM:
        pass

    @overload
    def tqdm(self, *, msg: str = "") -> TQDM:
        pass

    def tqdm(self, iter: Iterable = None, msg: str = "", *, length=None, immediate=False):
        if iter is not None:
            if length is None:
                try:
                    length = len(iter)
                except TypeError:
                    length = 0
        label = self.progress_cnt
        tqdm = TQDM((lambda percent, msg: self.tqdm_signal.emit(label, percent, msg)),
                    iter, length, msg)
        if immediate:
            tqdm.showMsg()
        self.progress_cnt += 1
        return tqdm

    def set_busy(self, busy: bool):
        if busy ^ self._busy:
            self._busy = busy
            self.busy_signal.emit(busy)
            if not busy:
                self.progress_cnt = 0

    @property
    def busy(self):
        return self._busy


T = TypeVar("T")


class TQDM(Generic[T]):
    def __init__(self, callback_func, iter: Iterable = None, length: int = 0, msg: str = "") -> None:
        self.callback_func = callback_func
        self.iter = iter
        self.msg = msg

        self.length = length
        self.now = 0

        self.begin_time = self.last_show_time = datetime.now()

    def showMsg(self):
        now = datetime.now()
        if (now - self.last_show_time).total_seconds() > .1:
            passed_time = now - self.begin_time
            if self.length > self.now:
                left_time = passed_time * (self.length - self.now) / self.now
                minute = int(left_time.total_seconds() / 60)
                second = format(left_time.total_seconds() % 60, '.2f')
                text = f"{self.msg} {self.now}/{self.length} ~{minute}:{second}"
                percent = 100 * self.now // self.length
            else:
                minute = int(passed_time.total_seconds() / 60)
                second = format(passed_time.total_seconds() % 60, '.2f')
                text = f"{self.msg} {self.now} {minute}:{second} passed"
                if self.length == self.now:
                    percent = 100
                else:
                    percent = 70
            self.callback_func(percent, text)
            self.last_show_time = now

    def start_time(self):
        self.begin_time = datetime.now()

    def update(self, step=1):
        self.now += step
        self.showMsg()

    def __iter__(self) -> Iterator[T]:
        self.start_time()
        for x in self.iter:
            self.update()
            yield x


class DataBindSignal(Generic[T]):
    def __init__(self, date_typ: Type[T]) -> None:
        self.handlers: dict = {}

    def connect(self, label: str, handler: Callable):
        self.handlers[label] = handler

    @overload
    def emit_except(self, except_label, arg: T):
        pass

    @overload
    def emit_except(self, except_label, *args, **kwargs):
        pass

    def emit_except(self, except_label, *args, **kwargs):
        for label, handler in self.handlers.items():
            if except_label != label:
                handler(*args, **kwargs)


class ValueGetter(Generic[T]):
    def __init__(self, value_typ: Type[T]) -> None:
        self.getter = None

    def connect(self, getter):
        self.getter = getter

    def get(self) -> T:
        if self.getter is None:
            raise RuntimeError("Haven't connect to a value getter")
        return self.getter()
