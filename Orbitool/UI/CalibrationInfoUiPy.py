from typing import Optional, Union

import numpy as np
from PyQt5 import QtCore, QtWidgets

from . import CalibrationInfoUi
from .manager import Manager
from .utils import get_tablewidget_selected_row

class Widget(QtWidgets.QWidget, CalibrationInfoUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

        self.manager.register_func("calibration info selected index", self.selected_index)
        self.manager.calibrationInfoWidget = self.tableWidget

    @property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def selected_index(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        if len(indexes) == 0:
            return 0
        return indexes[0]