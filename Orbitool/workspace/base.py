from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, Iterable, Type, TypeVar

from h5py import Group

from ..structures import BaseStructure, register_handler, StructureTypeHandler, get_handler
from ..structures.HDF5 import H5Obj, h5_brokens

T = TypeVar("T")


class Widget(H5Obj, Generic[T]):
    def __init__(self, obj, info_class: Type[T]) -> None:
        super().__init__(obj)
        self._info_class = info_class
        try:
            self.info: T = self.read(
                "info") if "info" in self else info_class()
        except:
            h5_brokens.append('/'.join((self._obj.name, "info")))
            self.info = info_class()
        handler: StructureTypeHandler = get_handler(UiState)
        try:
            self.ui_state: UiState = handler.read_from_h5(obj, "ui_state")
        except:
            h5_brokens.append('/'.join(self._obj.name, "ui_state"))
            self.ui_state = UiState({})

    def save(self):
        self.write("info", self.info)
        handler: StructureTypeHandler = get_handler(UiState)
        handler.write_to_h5(self._obj, "ui_state", self.ui_state)


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
    def FactoryStateGetter(cls, widget, keys: Iterable[str]):
        ins = cls()
        ins.fromNames(widget, keys)
        return ins

    @classmethod
    def FactoryFromComponents(cls, widget, components: Iterable):
        ins = cls()
        ins.fromComponents(widget, components)
        return cls

    def fromComponents(self, widget, components: Iterable):
        getter = UiNameGetter(widget)
        getter.register_components(components)
        self.fromNames(widget, getter.registered)

    def fromNames(self, widget, keys):
        states = {}
        for key in keys:
            if hasattr(widget, key):
                o = getattr(widget, key)
                typ = type(o)
                handler = state_handlers.get(typ, None)
                if not handler:
                    continue
                states[key] = handler.get(o)
        self.states = states

    def set_state(self, widget):
        for key, state in self.states.items():
            if hasattr(widget, key):
                o = getattr(widget, key)
                state_handlers[type(o)].set(o, state)


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


def init_handlers():
    global state_handlers
    from PyQt5.QtWidgets import (
        QCheckBox, QDateTimeEdit, QDoubleSpinBox, QLineEdit,
        QSpinBox, QRadioButton, QComboBox, QSlider)

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
        @staticmethod
        def get(obj: QDateTimeEdit) -> str:
            return obj.dateTime().toPyDateTime().isoformat()

        @staticmethod
        def set(obj: QDateTimeEdit, value: str):
            obj.setDateTime(datetime.fromisoformat(value))
    state_handlers[QDateTimeEdit] = DataTimeEditHandler

    class LineEditHandler(BaseStateHandler):
        @staticmethod
        def get(obj: QLineEdit) -> str:
            return obj.text()

        @staticmethod
        def set(obj: QLineEdit, value: str):
            obj.setText(value)
    state_handlers[QLineEdit] = LineEditHandler

    class ComboBoxHandler(BaseStateHandler):
        @staticmethod
        def get(obj: QComboBox) -> str:
            return obj.currentText()

        @staticmethod
        def set(obj: QComboBox, value: str):
            obj.setCurrentText(value)
    state_handlers[QComboBox] = ComboBoxHandler

    class SliderHandler(BaseStateHandler):
        @staticmethod
        def get(obj: QSlider) -> str:
            return obj.value()

        @staticmethod
        def set(obj: QSlider, value: str):
            obj.setValue(int(value))
    state_handlers[QSlider] = SliderHandler


init_handlers()
