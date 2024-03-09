from datetime import datetime

from .base import state_handlers, BaseStateHandler

def init_handlers():
    from PyQt6.QtWidgets import (
        QCheckBox, QDateTimeEdit, QDoubleSpinBox, QLineEdit,
        QSpinBox, QRadioButton, QComboBox, QSlider, QGroupBox) 

    class CheckBoxHandler(BaseStateHandler):
        @staticmethod
        def get(obj: QCheckBox | QGroupBox | QRadioButton) -> str:
            return "checked" if obj.isChecked() else "unchecked"

        @staticmethod
        def set(obj: QCheckBox | QGroupBox | QRadioButton, value):
            if value == "checked":
                obj.setChecked(True)
            elif value == "unchecked":
                obj.setChecked(False)
    state_handlers[QCheckBox] = CheckBoxHandler
    state_handlers[QRadioButton] = CheckBoxHandler
    state_handlers[QGroupBox] = CheckBoxHandler


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
            return str(obj.value())

        @staticmethod
        def set(obj: QSlider, value: str):
            obj.setValue(int(value))
    state_handlers[QSlider] = SliderHandler
