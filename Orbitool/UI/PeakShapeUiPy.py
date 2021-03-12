from typing import Union, Optional
from . import PeakShapeUi
from PyQt5 import QtWidgets, QtCore

from .manager import BaseWidget, state_node, Thread
from . import component


class Widget(QtWidgets.QWidget, PeakShapeUi.Ui_Form, BaseWidget):
    callback = QtCore.pyqtSignal()

    def __init__(self, widget_root, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.widget_root = widget_root
        
    def setupUi(self, Form):
        super().setupUi(Form)
        
        self.plot = component.Plot(self.widget)