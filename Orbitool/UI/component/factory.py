from typing import Callable, Union
from PyQt5 import QtWidgets, QtCore, QtGui


def CheckBox(checked: bool, text: str="", enable: bool = True, direction: QtCore.Qt.LayoutDirection = QtCore.Qt.LayoutDirection.LayoutDirectionAuto) -> QtWidgets.QCheckBox:
    box = QtWidgets.QCheckBox(text)
    box.setChecked(checked)
    box.setEnabled(enable)
    box.setLayoutDirection(direction)
    return box


def SpinBox(minimum: int, maximum: int, step: int, value: int, enable: bool = True) -> QtWidgets.QDoubleSpinBox:
    box = QtWidgets.QSpinBox()
    box.setMinimum(minimum)
    box.setMaximum(maximum)
    box.setSingleStep(step)
    box.setValue(value)
    box.setEnabled(enable)
    return box


def DoubleSpinBox(minimum: float, maximum: float, decimals: int, step: float, value: float, enable: bool = True) -> QtWidgets.QDoubleSpinBox:
    box = QtWidgets.QDoubleSpinBox()
    box.setMinimum(minimum)
    box.setMaximum(maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    box.setEnabled(enable)
    return box


def PushButton(text: int, clicked: Union[Callable, None] = None):
    btn = QtWidgets.QPushButton(text)
    if clicked:
        btn.clicked.connect(clicked)
    return btn


def ToolButton(icon: QtGui.QIcon, clicked: Union[Callable, None] = None):
    btn = QtWidgets.QToolButton()
    btn.setIcon(icon)
    if clicked:
        btn.clicked.connect(clicked)
    return btn
