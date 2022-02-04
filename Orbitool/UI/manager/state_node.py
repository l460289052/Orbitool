import functools
import logging
from enum import Enum
from typing import Any, Callable, Generator, overload
from PyQt5 import QtCore

from ... import get_config
from ..utils import showInfo, sleep
from .manager import Manager
from .thread import MultiProcess, Thread, threadtype


class NodeType(Enum):
    Root = 0
    Except = 1
    ThreadEnd = 2


# w x a n
# n: no set and no reset
_busy_check = {'w'}
_busy_set = {'w', 'x'}
_busy_reset = {'w', 'x', 'a'}


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
        mode: 'w': check and set busy; 'x': set busy without check; 'a': not check busy; 'e': only catch exception
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
        self._cached = None
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
        def decorator(selfWidget, *args, **kwargs):
            manager: Manager = selfWidget.manager
            if not manager.busy:
                if self._mode in _busy_set:
                    manager.set_busy(True)
                    sleep(.05)
            elif self._mode in _busy_check:
                # if manager.process_pool.
                # showInfo("Wait for process or abort", 'busy')
                # else:
                showInfo("Wait for process", 'busy')
                return
            try:
                ret = func(
                    selfWidget, *args, **kwargs) if self._withArgs else func(selfWidget)
                if isinstance(ret, Generator):
                    generator = ret

                    def run_send(result):
                        try:
                            if result:
                                result = result[0]

                                if isinstance(result, Exception):
                                    raise result
                            to_be_finished = generator.send(result)

                            if isinstance(to_be_finished, tuple):
                                to_be_finished, msg = to_be_finished
                            else:
                                msg = "processing"

                            manager.msg.emit(msg)

                            if not isinstance(to_be_finished, QtCore.QThread):
                                thread = Thread(to_be_finished)
                            else:
                                thread = to_be_finished
                            thread.set_tqdmer(manager.tqdm)
                            thread.finished.connect(run_send)
                            manager.running_thread = thread
                            if get_config().DEBUG:
                                thread.run()
                            else:
                                thread.start()
                        except StopIteration:
                            manager.set_busy(False)
                        except Exception as e:
                            logger = logging.getLogger("Orbitool")
                            logger.error(str(e), exc_info=e)
                            showInfo(str(e))
                            if (tmpfunc := self.except_node.func):
                                tmpfunc(selfWidget)
                            elif self._mode in _busy_reset:
                                manager.set_busy(False)

                    run_send(None)

                elif self._mode in _busy_reset:
                    manager.set_busy(False)
            except Exception as e:
                logger = logging.getLogger("Orbitool")
                logger.error(str(e), exc_info=e)
                showInfo(str(e))
                if (tmpfunc := self.except_node.func):
                    tmpfunc(selfWidget)
                elif self._mode in _busy_reset:
                    manager.set_busy(False)

        return decorator

    @func.setter
    def func(self, func):
        assert self._func is None
        if func is None:
            return
        self._func = func
        self.except_node = node(
            self._root, self, NodeType.Except, mode='a' if self._mode != 'e' else 'e')

    def __call__(self, func):
        self.func = func
        return self._root

    @functools.lru_cache(None)
    def __get__(self, obj, objtype=None):
        if obj is None or isinstance(obj, node):
            return self
        return functools.partial(self.func, obj)
