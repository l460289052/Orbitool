from typing import Any, Dict, Generic, Iterable, Type, TypeVar

from h5py import Group

from ..structures import BaseStructure, register_handler, StructureTypeHandler, get_handler, field

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


class UiState:
    def __init__(self, states: Dict[str, str] = None) -> None:
        self.states = states or {}

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


class UiStateHandler(StructureTypeHandler):
    def read_from_h5(self, h5group: Group, key: str):
        if key in h5group:
            states = dict(h5group[key].attrs.items())
        else:
            states = {}
        return UiState(states)

    def write_to_h5(self, h5group: Group, key: str, value: UiState):
        if key in h5group:
            del h5group[key]
        group = h5group.create_group(key)
        for key, state in value.states.items():
            group.attrs[key] = state


register_handler(UiState, UiStateHandler)


class BaseStateHandler:
    @staticmethod
    def get(obj) -> str:
        pass

    @staticmethod
    def set(obj, value: str):
        pass


state_handlers: Dict[Type, BaseStateHandler] = {}


class BaseInfo(BaseStructure):
    h5_type = "base info"
    ui_state: UiState = field(UiState)
