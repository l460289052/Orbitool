from PyQt5 import QtWidgets


def CheckBoxFactory(checked: bool) -> QtWidgets.QCheckBox:
    box = QtWidgets.QCheckBox()
    box.setChecked(checked)
    return box


def DoubleSpinBoxFactory(minimum: float, maximum: float, decimals: int, step: float, value: float) -> QtWidgets.QDoubleSpinBox:
    box = QtWidgets.QDoubleSpinBox()
    box.setMinimum(minimum)
    box.setMaximum(maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    return box
