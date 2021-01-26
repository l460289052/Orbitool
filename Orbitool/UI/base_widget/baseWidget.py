from functools import wraps
import traceback
import multiprocessing
import threading

from Orbitool.utils import logger

from Orbitool.structures import WorkSpace

from Orbitool.UI.utils import showInfo


class BaseWidget:
    def __init__(self, getWorkspace, getProcesspool, thread) -> None:
        self.getWorkspace = getWorkspace
        self.getProcesspool = getProcesspool
        self._thread = thread
        self.busy = False

    @property
    def workspace(self) -> WorkSpace:
        return self.getWorkspace()

    def setBusy(self, busy=True):
        if self.busy and busy:
            return False
        self.busy = busy
        return True

    @property
    def processpool(self) -> multiprocessing.Pool:
        return self.getProcesspool()
    
    @property
    def thread(self):
        return self._thread.get()

    @thread.setter
    def thread(self, value):
        return self._thread.set(value)

