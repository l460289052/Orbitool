import numpy as np
from PyQt5 import QtWidgets


def set_header_sizes(header: QtWidgets.QHeaderView, sizes: list):
    list(map(header.resizeSection, range(len(sizes)), sizes))


def get_tablewidget_selected_row(tableWidget: QtWidgets.QTableWidget):
    return np.unique([index.row() for index in tableWidget.selectedIndexes()])