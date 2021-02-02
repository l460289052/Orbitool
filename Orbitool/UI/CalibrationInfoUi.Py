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
        self.resultTableWidget = QtWidgets.QTableWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resultTableWidget.sizePolicy().hasHeightForWidth())
        self.resultTableWidget.setSizePolicy(sizePolicy)
        self.resultTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.resultTableWidget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.resultTableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.resultTableWidget.setObjectName("resultTableWidget")
        self.resultTableWidget.setColumnCount(0)
        self.resultTableWidget.setRowCount(0)
        self.resultTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.resultTableWidget)
        self.infoExportPushButton = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.infoExportPushButton.sizePolicy().hasHeightForWidth())
        self.infoExportPushButton.setSizePolicy(sizePolicy)
        self.infoExportPushButton.setObjectName("infoExportPushButton")
        self.verticalLayout.addWidget(self.infoExportPushButton)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.showSpectrumPushButton.setText(_translate("Form", "Show selected spectrum"))
        self.showSelectedPushButton.setText(_translate("Form", "Show selected results"))
        self.showAllPushButton.setText(_translate("Form", "Show all calibration info"))
        self.infoExportPushButton.setText(_translate("Form", "Export all info"))

