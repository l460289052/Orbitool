from typing import Optional
from . import TimeseriesUi
from PyQt5 import QtWidgets

from .manager import Manager, state_node


class Widget(QtWidgets.QWidget, TimeseriesUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
