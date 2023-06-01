from copy import deepcopy
from enum import Enum
import typing
from PyQt5 import QtCore, QtGui, QtWidgets
from .SettingUi import Ui_Dialog
from . import GeneralTabUiPy
from Orbitool import setting


class OptTab(Enum):
    General = "General"


class Dialog(QtWidgets.QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.init()

    def init(self):
        listWidget = self.ui.listWidget
        icon_getter = self.style().standardIcon
        ICONS = QtWidgets.QStyle.StandardPixmap
        options = [
            (icon_getter(ICONS.SP_FileDialogInfoView), OptTab.General.value)
        ]
        for icon, text in options:
            listWidget.addItem(
                QtWidgets.QListWidgetItem(icon, text))
        listWidget.itemClicked.connect(self.change_current_tab)

        self.tmp_setting = deepcopy(setting)
        self.show_tab(OptTab.General)
        self.current_tab: OptTab = OptTab.General
        self.accepted.connect(self.update_global_setting)

    def show_tab(self, tab: OptTab):
        ui = self.ui
        if tab == OptTab.General:
            self.current_widget = GeneralTabUiPy.Tab(ui.scrollAreaWidgetContents, self.tmp_setting)
            ui.scrollAreaLayout.addWidget(self.current_widget)
        elif True:
            pass
    
    def stash_tab(self):
        if self.current_tab is None:
            return
        self.current_widget.stash_setting(self.tmp_setting)
        self.ui.scrollAreaLayout.removeWidget(self.current_widget)

    def change_current_tab(self, item: QtWidgets.QListWidgetItem):
        tab = OptTab(item.text())
        self.stash_tab()
        self.show_tab(tab)

    def update_global_setting(self) -> None:
        self.stash_tab()
        setting.update_from(self.tmp_setting)
        setting.save_setting()