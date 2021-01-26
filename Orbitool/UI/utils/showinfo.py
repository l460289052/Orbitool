from PyQt5 import QtWidgets

def showInfo(content:str, cap=None):
    QtWidgets.QMessageBox.information(None, cap if cap is not None else 'info', str(content))