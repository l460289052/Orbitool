# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\Orbitool\UI\SpectraList.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(261, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.comboBox = QtWidgets.QComboBox(Form)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout_2.addWidget(self.comboBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.tableWidget)
        self.splitPushButton = QtWidgets.QPushButton(Form)
        self.splitPushButton.setObjectName("splitPushButton")
        self.verticalLayout.addWidget(self.splitPushButton)
        self.exportPushButton = QtWidgets.QPushButton(Form)
        self.exportPushButton.setObjectName("exportPushButton")
        self.verticalLayout.addWidget(self.exportPushButton)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "show spectra after"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "start time"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "end time"))
        self.splitPushButton.setText(_translate("Form", "split selected spectrum to list"))
        self.exportPushButton.setText(_translate("Form", "export all spectra"))

