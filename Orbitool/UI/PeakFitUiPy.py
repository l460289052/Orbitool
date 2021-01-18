from typing import Optional
from . import PeakFitUi
from PyQt5 import QtWidgets, QtCore

class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    def __init__(self, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)