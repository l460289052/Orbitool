from functools import wraps
from typing import Callable, Dict

from PyQt5.QtCore import QThread, pyqtSignal, QObject

from ...workspace import WorkSpace
from ..utils import showInfo
from ..component import Plot


class Manager(QObject):
    """
    storage common resources
    """
    inited_or_restored = pyqtSignal()
    save = pyqtSignal()
    busy_signal = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.running_thread: QThread = None
        self.workspace: WorkSpace = None
        self._busy: bool = True
        self._func: Dict[str, Callable] = {}

        self.calibrationPlot: Plot = None

    def set_busy(self, busy: bool):
        if busy ^ self._busy:
            self._busy = busy
            self.busy_signal.emit(busy)

    def register_func(self, key: str, func: Callable):
        self._func[key] = func

    def fetch_func(self, key: str):
        return self._func.get(key, lambda x: x)

    @property
    def busy(self):
        return self._busy
