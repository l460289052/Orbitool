from typing import Optional, Union

from PyQt5 import QtCore, QtWidgets

from . import PeakFitFloatUi


class Widget(QtWidgets.QWidget, PeakFitFloatUi.Ui_Form):
    callback = QtCore.pyqtSignal()

    def __init__(self, manager, peak_index: int) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
