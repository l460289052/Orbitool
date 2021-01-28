from typing import Any, Callable
import functools
import traceback
import logging
from enum import Enum

from Orbitool import config
from Orbitool.UI.utils import showInfo

from .base_widget import BaseWidget
from .thread import Thread, MultiProcess, threadtype


class NodeType(Enum):
    Root = 0
    Except = 1
    ThreadEnd = 2


class node:
    def __init__(self, func=None, root=None, nodeType: NodeType = NodeType.Root, *, withArgs=False) -> None:
        self._func = None
        self._nodeType = nodeType
        self._withArgs = withArgs
        self._root: node = self if root is None else root

        self.func: Callable = func

    @property
    def func(self):
        func = self._func
        if func is None:
            return None

        @functools.wraps(func)
        def decorator(selfWidget: BaseWidget, *args, **kwargs):
            if self._root is None:
                if selfWidget.busy.get():
                    # if manager.process_pool.
                        # showInfo("Wait for process or abort", 'busy')
                    # else:
                    showInfo("Wait for process", 'busy')
                    return
                else:
                    selfWidget.busy.set(True)
            try:
                ret = func(selfWidget, *args, **
                           kwargs) if self._withArgs else func(selfWidget)
                if self.thread_node.func is not None:
                    ttype, *ret = ret
                    thread = Thread(
                        ret) if ttype == threadtype.thread else MultiProcess(ret)
                    selfWidget.thread = thread
                    # thread.sendStatus.connect()
                    thread.finished.connect(functools.partial(
                        self.thread_node.func, selfWidget))
                    thread.start()
                else:
                    selfWidget.busy.set(False)
            except Exception as e:
                showInfo(str(e))
                logging.error(str(e), exc_info=e)
                if self.except_node.func is not None:
                    self.except_node.func(selfWidget)
                else:
                    selfWidget.busy.set(False)
        return decorator

    @func.setter
    def func(self, func):
        assert self._func is None
        if func is None:
            return
        self._func = func
        self.except_node = node(None, self._root, NodeType.Except)
        self.thread_node = node(
            None, self._root, NodeType.ThreadEnd, withArgs=True)

    def __call__(self, func):
        self.func = func
        return self._root

    def __get__(self, obj, objtype=None):
        if obj is None or isinstance(obj, node):
            return self
        return functools.partial(self.func, obj)
