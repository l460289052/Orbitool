from typing import Optional
from . import TimeseriesUi
from PyQt5 import QtWidgets


class Widget(QtWidgets.QWidget, TimeseriesUi.Ui_Form):
    def __init__(self, parent: Optional['QWidget']=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)