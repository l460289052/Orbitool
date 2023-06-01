import typing
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget
from Orbitool.config import _Setting

class BaseTab(QtWidgets.QWidget):
    def stash_setting(self, setting: _Setting):
        pass