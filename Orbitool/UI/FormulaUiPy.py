from typing import Union, Optional
from . import FormulaUi

from PyQt5 import QtWidgets, QtCore
from .manager import Manager


class Widget(QtWidgets.QWidget, FormulaUi.Ui_Form):
    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.setupUi(self)
        
    def setupUi(self, Form):
        super().setupUi(Form)
        
        self.negativeRadioButton.setChecked(True)

        
