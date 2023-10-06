from typing import Any, Dict, Generic, Iterable, Type, TypeVar

from Orbitool.base import BaseStructure, BaseDatasetStructure

T = TypeVar("T")


class UiNameGetter:
    def __init__(self, widget) -> None:
        id_dict = {}
        for key in dir(widget):
            id_dict[id(getattr(widget, key))] = key
        self.id_dict = id_dict
        self.registered = set()

    def register_component(self, component):
        if (key := self.id_dict.get(id(component), None)) is not None:
            self.registered.add(key)

    def register_components(self, components: Iterable):
        list(map(self.register_component, components))


class UiState(BaseDatasetStructure):
    states: Dict[str, str] = {}

    def store_state(self, ui: object):
        types = tuple(state_handlers)
        states = {}
        for key, attr in ui.__dict__.items():
            if isinstance(attr, types):
                handler = state_handlers.get(type(attr), None)
                if handler:
                    states[key] = handler.get(attr)
        self.states = states

    def restore_state(self, widget):
        for key, state in self.states.items():
            attr = getattr(widget, key, None)
            if attr:
                state_handlers[type(attr)].set(attr, state)


class BaseStateHandler:
    @staticmethod
    def get(obj) -> str:
        pass

    @staticmethod
    def set(obj, value: str):
        pass


state_handlers: Dict[Type, BaseStateHandler] = {}


class BaseInfo(BaseStructure):
    ui_state: UiState = UiState()
