# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\Orbitool\UI\Main.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks|QtWidgets.QMainWindow.AllowTabbedDocks|QtWidgets.QMainWindow.AnimatedDocks|QtWidgets.QMainWindow.GroupedDragging|QtWidgets.QMainWindow.VerticalTabs)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)
        self.processWidget = QtWidgets.QWidget(self.centralwidget)
        self.processWidget.setObjectName("processWidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.processWidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.progressBar = QtWidgets.QProgressBar(self.processWidget)
        self.progressBar.setMaximum(123)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout_2.addWidget(self.progressBar)
        self.abortPushButton = QtWidgets.QPushButton(self.processWidget)
        self.abortPushButton.setObjectName("abortPushButton")
        self.horizontalLayout_2.addWidget(self.abortPushButton)
        self.verticalLayout.addWidget(self.processWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 20))
        self.menubar.setObjectName("menubar")
        self.menuWorkspace = QtWidgets.QMenu(self.menubar)
        self.menuWorkspace.setObjectName("menuWorkspace")
        self.menuConfig = QtWidgets.QMenu(self.menubar)
        self.menuConfig.setObjectName("menuConfig")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.workspaceSaveAction = QtWidgets.QAction(MainWindow)
        self.workspaceSaveAction.setObjectName("workspaceSaveAction")
        self.workspaceLoadAction = QtWidgets.QAction(MainWindow)
        self.workspaceLoadAction.setObjectName("workspaceLoadAction")
        self.workspaceSaveAsAction = QtWidgets.QAction(MainWindow)
        self.workspaceSaveAsAction.setObjectName("workspaceSaveAsAction")
        self.configLoadAction = QtWidgets.QAction(MainWindow)
        self.configLoadAction.setObjectName("configLoadAction")
        self.configSaveAction = QtWidgets.QAction(MainWindow)
        self.configSaveAction.setObjectName("configSaveAction")
        self.menuWorkspace.addAction(self.workspaceLoadAction)
        self.menuWorkspace.addAction(self.workspaceSaveAction)
        self.menuWorkspace.addAction(self.workspaceSaveAsAction)
        self.menuConfig.addAction(self.configLoadAction)
        self.menuConfig.addAction(self.configSaveAction)
        self.menubar.addAction(self.menuWorkspace.menuAction())
        self.menubar.addAction(self.menuConfig.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.progressBar.setFormat(_translate("MainWindow", "%v/%m"))
        self.abortPushButton.setText(_translate("MainWindow", "Abort"))
        self.menuWorkspace.setTitle(_translate("MainWindow", "Workspace"))
        self.menuConfig.setTitle(_translate("MainWindow", "Config"))
        self.workspaceSaveAction.setText(_translate("MainWindow", "Save"))
        self.workspaceSaveAction.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.workspaceLoadAction.setText(_translate("MainWindow", "Load"))
        self.workspaceSaveAsAction.setText(_translate("MainWindow", "Save as"))
        self.configLoadAction.setText(_translate("MainWindow", "Load"))
        self.configSaveAction.setText(_translate("MainWindow", "Save"))

