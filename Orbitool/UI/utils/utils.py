from csv import QUOTE_ALL
from typing import Any, Union
from typing_extensions import deprecated
import numpy as np
from PyQt6 import QtWidgets, QtCore

from Orbitool.UI.setting.FileTabUiPy import Tab

from . import test


def set_header_sizes(header: QtWidgets.QHeaderView, sizes: list):
    list(map(header.resizeSection, range(len(sizes)), sizes))


@deprecated("Use TableUtils.getSelectedRow instead")
@test.override_input
def get_tablewidget_selected_row(tableWidget: QtWidgets.QTableWidget) -> np.ndarray:
    return np.unique([index.row() for index in tableWidget.selectedIndexes()])


def sleep(second):
    if second > 0:
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()
        timer.timeout.connect(loop.quit)
        timer.start(int(second * 1000))
        loop.exec()

class TableUtils:
    @staticmethod
    def clear(table: QtWidgets.QTableWidget):
        table.clearContents()
        table.setRowCount(0)

    @staticmethod
    def clearAndSetRowCount(table: QtWidgets.QTableWidget, count: int):
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(count)

    @staticmethod
    def setRow(table: QtWidgets.QTableWidget, row: int, *cells: Union[str, Any]):
        for column, cell in enumerate(cells):
            table.setItem(row, column, QtWidgets.QTableWidgetItem(str(cell)))

    @staticmethod
    def getSelectedRow(table: QtWidgets.QTableWidget):
        return np.unique([index.row() for index in table.selectedIndexes()])
