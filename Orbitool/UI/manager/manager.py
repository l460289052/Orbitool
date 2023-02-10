from __future__ import annotations
from contextlib import contextmanager

import weakref
from datetime import datetime
from functools import wraps
from typing import (
    Callable, Dict, Generic, Iterable, Iterator, Type, TypeVar,
    List, overload, Set, Sized)
from types import MethodType

import numpy as np
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QTableWidget

from ...workspace import WorkSpace


class BindData:
    def __init__(self) -> None:
        self.peak_fit_left_index: DataBindSignal[int] = DataBindSignal()


class Values:
    def __init__(self) -> None:
        self.calibration_info_selected_index: ValueGetter[int] = ValueGetter()
        self.mass_list_selected_indexes: ValueGetter[np.ndarray] = ValueGetter(
        )
        self.spectra_list_selected_index: ValueGetter[int] = ValueGetter()
        self.peak_list_selected_true_index: ValueGetter[List[int]] = ValueGetter()


class Signals:
    def __init__(self) -> None:
        self.peak_refit_finish = MySignal()
        self.peak_list_show = MySignal()


class Manager(QObject):
    """
    storage common resources
    """
    busy_signal = pyqtSignal(bool)
    msg = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.running_thread: QThread = None
        self.workspace: WorkSpace = None
        self._busy: bool = True

        self.formulas_result_win: QMainWindow = None
        self.calibration_detail_win: QMainWindow = None
        self.peak_float_wins: Dict[int, QMainWindow] = {}

        self.tqdm = TQDMER()
        self.busy_signal.connect(self.tqdm.reinit)

        self.init_or_restored = MySignal()  # for exception catch
        self.save = MySignal()  # for exception catch
        self.signals = Signals()

        self.bind = BindData()
        self.getters = Values()

    def set_busy(self, busy: bool):
        if busy ^ self._busy:
            self._busy = busy
            self.busy_signal.emit(busy)

    @property
    def busy(self):
        return self._busy

    @contextmanager
    def not_check(self):
        busy = self.busy
        self.set_busy(False)
        try:
            yield
        except:
            raise
        finally:
            self.set_busy(busy)


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
        if (now - self.last_show_time).total_seconds() > .01 or self.length < 1000:
            passed_time = now - self.begin_time
            if self.length > self.now:
                if self.now:
                    left_time = passed_time * \
                        (self.length - self.now) / self.now
                    minute = int(left_time.total_seconds() / 60)
                    second = format(left_time.total_seconds() % 60, '.2f')
                else:
                    minute = "inf"
                    second = "inf"
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


class TQDMER(QObject):
    tqdm_signal = pyqtSignal(int, int, str)  # label, percent, msg

    def __init__(self) -> None:
        super().__init__()
        self.progress_cnt = 0

    @overload
    def __call__(self, iter: Iterable[T], msg: str = "") -> TQDM[T]:
        pass

    @overload
    def __call__(self, iter: Iterable[T], msg: str = "", *, length: int = 0, immediate=False) -> TQDM[T]:
        pass

    @overload
    def __call__(self, *, msg: str = "", length: int = 0) -> TQDM:
        pass

    @overload
    def __call__(self, *, msg: str = "") -> TQDM:
        pass

    def __call__(self, iter: Iterable = None, msg: str = "", *, length=None, immediate=False):
        if iter is not None:
            if length is None:
                if isinstance(iter, Sized):
                    length = len(iter)
                else:
                    length = 0
        label = self.progress_cnt
        tqdm = TQDM((lambda percent, msg: self.tqdm_signal.emit(label, percent, msg)),
                    iter, length, msg)
        if immediate:
            tqdm.showMsg()
        self.progress_cnt += 1
        return tqdm

    def reinit(self, reinit: bool = True):
        if reinit:
            self.progress_cnt = 0


def get_callable_weak_ref(handler, callback=None):
    if isinstance(handler, MethodType):
        return weakref.WeakMethod(handler, callback)
    else:
        return weakref.ref(handler, callback)


class MySignal(Generic[T]):
    def __init__(self) -> None:
        self.handlers: Set[weakref.ReferenceType] = set()

    def connect(self, handler: Callable):
        self.handlers.add(get_callable_weak_ref(handler, self.remove_ref))

    def disconnect(self, handler: Callable):
        ref = get_callable_weak_ref(handler)
        self.remove_ref(ref)

    def remove_ref(self, handler_ref):
        self.handlers.discard(handler_ref)

    @overload
    def emit(self, args: T): ...
    @overload
    def emit(self, *args, **kwargs): ...

    def emit(self, *args, **kwargs):
        # emit
        for handler in self.handlers:
            handler()(*args, **kwargs)


class DataBindSignal(Generic[T]):
    def __init__(self) -> None:
        self.handlers: Dict[str, weakref.ReferenceType] = {}

    def connect(self, label: str, handler: Callable):
        self.handlers[label] = get_callable_weak_ref(
            handler, lambda x: self.remove_label(label))

    def remove_label(self, label):
        self.handlers.pop(label, None)

    @overload
    def emit_except(self, except_label, arg: T):
        pass

    @overload
    def emit_except(self, except_label, *args, **kwargs):
        pass

    def emit_except(self, except_label, *args, **kwargs):
        for label, handler in self.handlers.items():
            if except_label != label:
                handler()(*args, **kwargs)

    def emit(self, *args, **kwargs):
        for handler in self.handlers.values():
            handler()(*args, **kwargs)


class ValueGetter(Generic[T]):
    def __init__(self) -> None:
        self.getter = None

    def connect(self, getter):
        self.getter = getter

    def get(self) -> T:
        if self.getter is None:
            raise RuntimeError("Haven't connect to a value getter")
        return self.getter()
