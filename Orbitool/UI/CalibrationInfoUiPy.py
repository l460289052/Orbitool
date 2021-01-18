from typing import Union, Optional
from . import CalibrationInfoUi
from PyQt5 import QtWidgets, QtCore


class Widget(QtWidgets.QWidget, CalibrationInfoUi.Ui_Form):
    def __init__(self, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
