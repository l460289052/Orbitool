from functools import wraps
from datetime import datetime
from typing import Callable, Dict, Iterable, overload, TypeVar, Generic, Iterator
import random


from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QProgressBar

from ...workspace import WorkSpace
from ..utils import showInfo
from ..component import Plot

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
                percent = .9
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
        self._func: Dict[str, Callable] = {}
        self.progress_cnt = 0

        self.calibrationPlot: Plot = None

    @overload
    def tqdm(self, iter: Iterable[T], msg: str = "") -> TQDM[T]:
        pass

    @overload
    def tqdm(self, iter: Iterable[T], msg: str = "", *, length: int = 0) -> TQDM[T]:
        pass

    @overload
    def tqdm(self, *, msg: str = "", length: int = 0) -> TQDM:
        pass

    @overload
    def tqdm(self, *, msg: str = "") -> TQDM:
        pass

    def tqdm(self, iter: Iterable = None, msg: str = "", *, length=None):
        if iter is not None:
            if length is None:
                try:
                    length = len(iter)
                except TypeError:
                    length = 0
        label = self.progress_cnt
        tqdm = TQDM((lambda percent, msg: self.tqdm_signal.emit(label, percent, msg)),
                    iter, length, msg)
        self.progress_cnt += 1
        return tqdm

    def set_busy(self, busy: bool):
        if busy ^ self._busy:
            self._busy = busy
            self.busy_signal.emit(busy)
            if not busy:
                self.progress_cnt = 0

    def register_func(self, key: str, func: Callable):
        self._func[key] = func

    def fetch_func(self, key: str):
        return self._func.get(key, lambda x: x)

    @property
    def busy(self):
        return self._busy
