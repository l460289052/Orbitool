from PyQt5 import QtWidgets


def set_header_sizes(header: QtWidgets.QHeaderView, sizes: list):
    list(map(header.resizeSection, range(len(sizes)), sizes))
