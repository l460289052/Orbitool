from typing import Any, Callable, overload
import functools
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
    """
    @thread_node
    def func(self, result, args)
    """
    @overload
    def __init__(self, func):
        pass

    @overload
    def __init__(self, *, withArgs=False, mode='w'):
        """

        mode: 'w': check and set busy; 'x': set busy without check; 'a': not check busy;
        """
        pass

    @overload
    def __init__(self, root=None, father=None, nodeType: NodeType = NodeType.Root, *, withArgs=False, mode='w'):
        pass

    def __init__(self, root=None, father=None, nodeType: NodeType = NodeType.Root, *, withArgs=False, mode='w') -> None:
        self._func = None
        self._withArgs = withArgs
        self._mode = mode
        self._nodeType = nodeType
        self._father: node = father
        if isinstance(root, node) or root is None:
            self._root: node = self if root is None else root
        else:
            self._root: node = self
            self.func: Callable = root

    @property
    def func(self):
        func = self._func
        if func is None:
            return None

        @functools.wraps(func)
        def decorator(selfWidget: BaseWidget, *args, **kwargs):
            if not selfWidget.busy:
                if self._mode != 'a':
                    selfWidget.busy = True
            elif self._mode == 'w':
                # if manager.process_pool.
                # showInfo("Wait for process or abort", 'busy')
                # else:
                showInfo("Wait for process", 'busy')
                return
            try:
                if self._nodeType == NodeType.ThreadEnd:
                    args = args[0]
                    if isinstance(args[0], Exception):
                        e = args[0]
                        logging.error(str(e), exc_info=e)
                        showInfo(str(e))
                        if (tmpfunc := self._father.except_node.func):
                            tmpfunc(selfWidget)
                        else:
                            selfWidget.busy = False
                        return
                    thread = func(selfWidget, *args)
                else:
                    thread = func(selfWidget, *args, **
                                  kwargs) if self._withArgs else func(selfWidget)

                if thread is not None and (tmpfunc := self.thread_node.func):
                    selfWidget.node_thread = thread
                    # thread.sendStatus.connect()
                    thread.finished.connect(
                        functools.partial(tmpfunc, selfWidget))
                    if config.DEBUG:
                        thread.run()
                    else:
                        thread.start()
                else:
                    selfWidget.busy = False
            except Exception as e:
                logging.error(str(e), exc_info=e)
                showInfo(str(e))
                if (tmpfunc := self.except_node.func):
                    tmpfunc(selfWidget)
                else:
                    selfWidget.busy = False

        return decorator

    @func.setter
    def func(self, func):
        assert self._func is None
        if func is None:
            return
        self._func = func
        self.except_node = node(self._root, self, NodeType.Except, mode='a')
        self.thread_node = node(
            self._root, self, NodeType.ThreadEnd, withArgs=True, mode='a')

    def __call__(self, func):
        self.func = func
        return self._root

    def __get__(self, obj, objtype=None):
        if obj is None or isinstance(obj, node):
            return self
        return functools.partial(self.func, obj)
