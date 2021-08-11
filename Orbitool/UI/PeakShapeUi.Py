# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\Orbitool\UI\PeakShape.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(499, 305)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.spinBox = QtWidgets.QSpinBox(Form)
        self.spinBox.setProperty("value", 50)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout.addWidget(self.spinBox)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.comboBox = QtWidgets.QComboBox(Form)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout.addWidget(self.comboBox)
        self.showPushButton = QtWidgets.QPushButton(Form)
        self.showPushButton.setObjectName("showPushButton")
        self.horizontalLayout.addWidget(self.showPushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.widget = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.verticalLayout.addWidget(self.widget)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.exportPushButton = QtWidgets.QPushButton(Form)
        self.exportPushButton.setObjectName("exportPushButton")
        self.horizontalLayout_3.addWidget(self.exportPushButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.cancelPushButton = QtWidgets.QPushButton(Form)
        self.cancelPushButton.setObjectName("cancelPushButton")
        self.horizontalLayout_3.addWidget(self.cancelPushButton)
        self.finishPushButton = QtWidgets.QPushButton(Form)
        self.finishPushButton.setObjectName("finishPushButton")
        self.horizontalLayout_3.addWidget(self.finishPushButton)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "use the highest N peaks"))
        self.label_2.setText(_translate("Form", "Peak distribution"))
        self.showPushButton.setText(_translate("Form", "&show"))
        self.showPushButton.setShortcut(_translate("Form", "Alt+S"))
        self.exportPushButton.setText(_translate("Form", "&Export peak shape info"))
        self.exportPushButton.setShortcut(_translate("Form", "Alt+E"))
        self.cancelPushButton.setToolTip(_translate("Form", "Ctrl+Z"))
        self.cancelPushButton.setText(_translate("Form", "Cancel removal"))
        self.cancelPushButton.setShortcut(_translate("Form", "Ctrl+Z"))
        self.finishPushButton.setToolTip(_translate("Form", "Return Key"))
        self.finishPushButton.setText(_translate("Form", "Finish and continue"))
        self.finishPushButton.setShortcut(_translate("Form", "Return"))

