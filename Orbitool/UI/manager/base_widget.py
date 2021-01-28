from functools import wraps
from multiprocessing.pool import Pool
from threading import Thread

from Orbitool.structures import WorkSpace
from Orbitool.UI.utils import showInfo


class Item:
    def __set_name__(self, owner, name):
        self.name = name
        self._name = '_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj if obj.widget_root is None else obj.widget_root, self._name)

    def __set__(self, obj, value):
        setattr(obj if obj.widget_root is None else obj.widget_root, self._name, value)


class ReadOnlyItem(Item):
    def __set__(self, obj, value):
        assert not hasattr(self, 'setted')
        self.setted = True
        return super().__set__(obj, value)


class Event:
    def __init__(self) -> None:
        self.value = None
        self.handlers = []

    def get(self):
        return self.value

    def set(self, value):
        if value != self.value:
            for handler in self.handlers:
                handler(value)
            self.value = value

    def add_handler(self, handler):
        assert callable(handler)
        self.handlers.append(handler)


class BaseWidget:
    thread: Thread = Item()
    process_pool: Pool = ReadOnlyItem()
    busy: Event = ReadOnlyItem()
    workspace: WorkSpace = Item()

    def __init__(self, root=None) -> None:
        self.widget_root: BaseWidget = root
        if root is None:
            self.busy = Event()
