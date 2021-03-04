from typing import Callable
from functools import wraps
from multiprocessing.pool import Pool

from PyQt5.QtCore import QThread, pyqtSignal

from Orbitool.structures import WorkSpace
from Orbitool.UI.utils import showInfo


class Item:
    def __set_name__(self, owner, name):
        self.name = name
        self._name = '_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj if obj.widget_root is None else obj.widget_root, self._name)

    def __set__(self, obj, value):
        setattr(obj if obj.widget_root is None else obj.widget_root,
                self._name, value)


class ReadOnlyItem(Item):
    def __set__(self, obj, value):
        assert not hasattr(self, 'setted')
        self.setted = True
        return super().__set__(obj, value)


class BaseWidget:
    node_thread: QThread = Item()
    process_pool: Pool = ReadOnlyItem()
    current_workspace: WorkSpace = Item()
    busy: bool = Item()
    inited: pyqtSignal = Item()

    def __init__(self, root=None) -> None:
        self.widget_root: BaseWidget = root
