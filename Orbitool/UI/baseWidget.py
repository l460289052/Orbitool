from functools import wraps
import traceback
import multiprocessing

from Orbitool import config
from Orbitool.utils import logger

from Orbitool.structures import WorkSpace

from .utils import showInfo


class BaseWidget:
    def __init__(self, getWorkspace, getProcesspool) -> None:
        self.getWorkspace = getWorkspace
        self.getProcesspool = getProcesspool
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


if config.DEBUG:
    def busy(withArgs=False):
        _withArgs = withArgs if isinstance(withArgs, bool) else False

        def decorator(func):
            @wraps(func)
            def funcrun(self: BaseWidget, *args, **kwargs):
                if not self.setBusy(True):
                    return
                if _withArgs:
                    func(self, *args, **kwargs)
                else:
                    func(self)
                self.setBusy(False)
            return funcrun
        return decorator if isinstance(withArgs, bool) else decorator(withArgs)

else:
    def busy(withArgs=False):
        _withArgs = withArgs if isinstance(withArgs, bool) else False

        def decorator(func):
            @wraps(func)
            def funcrun(self: BaseWidget, *args, **kwargs):
                if not self.setBusy(True):
                    return
                try:
                    if _withArgs:
                        func(self, *args, **kwargs)
                    else:
                        func(self)
                except Exception as e:
                    showInfo(str(e))
                    logger.error(str(e), traceback.format_exc())
                self.setBusy(False)
            return funcrun
        return decorator if isinstance(withArgs, bool) else decorator(withArgs)


def busyExcept(except_func: BaseWidget, withArgs=False):
    def busy(func):
        @wraps(func)
        def decorator(self, *args, **kwargs):
            if not self.setBusy(True):
                return
            try:
                if withArgs:
                    func(self, *args, **kwargs)
                else:
                    func(self)
            except Exception as e:
                showInfo(str(e))
                logger.error(str(e), traceback.format_exc())
                except_func(self)
            self.setBusy(False)
        return decorator
    return busy
