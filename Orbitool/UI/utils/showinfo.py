from PyQt5.QtWidgets import QMessageBox
BTN = QMessageBox.StandardButton

def showInfo(content:str, cap=None):
    QMessageBox.information(None, cap or 'info', str(content))

def confirm(content: str, cap=None):
    ret = QMessageBox.question(None, cap or 'confirm', content, BTN.Yes | BTN.No, BTN.Yes)
    return ret == BTN.Yes
