from typing import Union, Optional
from . import PeakShapeUi
from PyQt5 import QtWidgets, QtCore

from .manager import Manager, state_node, Thread
from . import component


class Widget(QtWidgets.QWidget, PeakShapeUi.Ui_Form):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.manager = manager

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = component.Plot(self.widget)
