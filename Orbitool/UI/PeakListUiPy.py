from typing import Optional, Union

from PyQt5 import QtCore, QtWidgets

from . import PeakListUi
from .manager import Manager


class Widget(QtWidgets.QWidget, PeakListUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
