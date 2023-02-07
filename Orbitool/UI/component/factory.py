from PyQt5 import QtWidgets, QtCore


def CheckBoxFactory(checked: bool, text: str, enable: bool = True, direction: QtCore.Qt.LayoutDirection = QtCore.Qt.LayoutDirection.LayoutDirectionAuto) -> QtWidgets.QCheckBox:
    box = QtWidgets.QCheckBox(text)
    box.setChecked(checked)
    box.setEnabled(enable)
    box.setLayoutDirection(direction)
    return box


def SpinBoxFactory(minimum: int, maximum: int, step: int, value: int, enable: bool = True) -> QtWidgets.QDoubleSpinBox:
    box = QtWidgets.QSpinBox()
    box.setMinimum(minimum)
    box.setMaximum(maximum)
    box.setSingleStep(step)
    box.setValue(value)
    box.setEnabled(enable)
    return box


def DoubleSpinBoxFactory(minimum: float, maximum: float, decimals: int, step: float, value: float, enable: bool = True) -> QtWidgets.QDoubleSpinBox:
    box = QtWidgets.QDoubleSpinBox()
    box.setMinimum(minimum)
    box.setMaximum(maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    box.setEnabled(enable)
    return box
