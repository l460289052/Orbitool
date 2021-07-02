# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\Orbitool\UI\CalibrationInfo.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.showSpectrumPushButton = QtWidgets.QPushButton(Form)
        self.showSpectrumPushButton.setObjectName("showSpectrumPushButton")
        self.verticalLayout.addWidget(self.showSpectrumPushButton)
        self.showSelectedPushButton = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showSelectedPushButton.sizePolicy().hasHeightForWidth())
        self.showSelectedPushButton.setSizePolicy(sizePolicy)
        self.showSelectedPushButton.setObjectName("showSelectedPushButton")
        self.verticalLayout.addWidget(self.showSelectedPushButton)
        self.showAllPushButton = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showAllPushButton.sizePolicy().hasHeightForWidth())
        self.showAllPushButton.setSizePolicy(sizePolicy)
        self.showAllPushButton.setObjectName("showAllPushButton")
        self.verticalLayout.addWidget(self.showAllPushButton)
        self.tableWidget = QtWidgets.QTableWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.tableWidget)
        self.exportPushButton = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.exportPushButton.sizePolicy().hasHeightForWidth())
        self.exportPushButton.setSizePolicy(sizePolicy)
        self.exportPushButton.setObjectName("exportPushButton")
        self.verticalLayout.addWidget(self.exportPushButton)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.showSpectrumPushButton.setText(_translate("Form", "Show selected spectrum"))
        self.showSelectedPushButton.setText(_translate("Form", "Show selected results"))
        self.showAllPushButton.setText(_translate("Form", "Show all calibration info"))
        self.exportPushButton.setText(_translate("Form", "Export all info"))

