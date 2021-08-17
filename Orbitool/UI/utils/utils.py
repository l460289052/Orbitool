import numpy as np
from PyQt5 import QtWidgets, QtCore

from . import test


def set_header_sizes(header: QtWidgets.QHeaderView, sizes: list):
    list(map(header.resizeSection, range(len(sizes)), sizes))


@test.override_input
def get_tablewidget_selected_row(tableWidget: QtWidgets.QTableWidget) -> np.ndarray:
    return np.unique([index.row() for index in tableWidget.selectedIndexes()])


def sleep(second):
    if second > 0:
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()
        timer.timeout.connect(loop.quit)
        timer.start(int(second * 1000))
        loop.exec_()
