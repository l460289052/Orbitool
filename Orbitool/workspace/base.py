from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, Iterable, Type, TypeVar

from h5py import Group

from ..structures.HDF5 import BaseSingleConverter, H5Obj, register_converter

T = TypeVar("T")


class Widget(H5Obj, Generic[T]):
    def __init__(self, obj, info_class: Type[T]) -> None:
        super().__init__(obj)
        self._info_class = info_class
        self.info: T = self.read("info") if "info" in self else info_class()
        self.ui_state: UiState = UiStateConverter.read_from_h5(obj, "ui_state")

    def save(self):
        self.write("info", self.info)
        UiStateConverter.write_to_h5(self._obj, "ui_state", self.ui_state)


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
    def __init__(self, states: Dict[str, str]) -> None:
        self.states = states

    @classmethod
    def FactoryStateGetter(cls, widget, keys: Iterable[str]) -> UiState:
        states = {}
        for key in keys:
            if hasattr(widget, key):
                o = getattr(widget, key)
                states[key] = state_handlers[type(o)].get(o)
        return cls(states)

    def set_state(self, widget):
        for key, state in self.states.items():
            if hasattr(widget, key):
                o = getattr(widget, key)
                state_handlers[type(o)].set(o, state)


class UiStateConverter(BaseSingleConverter):
    @staticmethod
    def read_from_h5(h5group: Group, key: str):
        if key in h5group:
            states = dict(h5group[key].attrs.items())
        else:
            states = {}
        return UiState(states)

    @staticmethod
    def write_to_h5(h5group: Group, key: str, value: UiState):
        if key in h5group:
            del h5group[key]
        group = h5group.create_group(key)
        for key, state in value.states.items():
            group.attrs[key] = state


register_converter(UiState, UiStateConverter)


class BaseStateHandler:
    @staticmethod
    def get(obj) -> str:
        pass

    @staticmethod
    def set(obj, value: str):
        pass


state_handlers: Dict[Type, BaseStateHandler] = {}


def init_handlers():
    global state_handlers
    from PyQt5.QtWidgets import (QCheckBox, QDateTimeEdit, QDoubleSpinBox,
                                 QLineEdit, QSpinBox, QRadioButton)

    class CheckBoxHandler(BaseStateHandler):
        @staticmethod
        def get(obj: QCheckBox) -> str:
            return "checked" if obj.isChecked() else "unchecked"

        @staticmethod
        def set(obj: QCheckBox, value):
            if value == "checked":
                obj.setChecked(True)
            elif value == "unchecked":
                obj.setChecked(False)
    state_handlers[QCheckBox] = CheckBoxHandler
    state_handlers[QRadioButton] = CheckBoxHandler

    class SpinBoxHandler(BaseStateHandler):
        @staticmethod
        def get(obj: QSpinBox) -> str:
            return str(obj.value())

        @staticmethod
        def set(obj: QSpinBox, value):
            obj.setValue(int(value))
    state_handlers[QSpinBox] = SpinBoxHandler

    class DoubleSpinBoxHandler(SpinBoxHandler):
        @staticmethod
        def set(obj: QDoubleSpinBox, value: str):
            obj.setValue(float(value))
    state_handlers[QDoubleSpinBox] = DoubleSpinBoxHandler

    class DataTimeEditHandler(BaseStateHandler):
        @ staticmethod
        def get(obj: QDateTimeEdit) -> str:
            return obj.dateTime().toPyDateTime().isoformat()

        @ staticmethod
        def set(obj: QDateTimeEdit, value: str):
            obj.setDateTime(datetime.fromisoformat(value))
    state_handlers[QDateTimeEdit] = DataTimeEditHandler

    class LineEditHandler(BaseStateHandler):
        @ staticmethod
        def get(obj: QLineEdit) -> str:
            return obj.text()

        @ staticmethod
        def set(obj: QLineEdit, value: str):
            obj.setText(value)
    state_handlers[QLineEdit] = LineEditHandler

init_handlers()