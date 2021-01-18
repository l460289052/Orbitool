# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Orbitool/UI\CatTimeseries.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(753, 494)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.timeSeriesCatSplitter = QtWidgets.QSplitter(Form)
        self.timeSeriesCatSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.timeSeriesCatSplitter.setObjectName("timeSeriesCatSplitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.timeSeriesCatSplitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_23 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_23.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_23.setObjectName("verticalLayout_23")
        self.csvAddPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.csvAddPushButton.setObjectName("csvAddPushButton")
        self.verticalLayout_23.addWidget(self.csvAddPushButton)
        self.horizontalLayout_33 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.label_31 = QtWidgets.QLabel(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_31.sizePolicy().hasHeightForWidth())
        self.label_31.setSizePolicy(sizePolicy)
        self.label_31.setObjectName("label_31")
        self.horizontalLayout_33.addWidget(self.label_31)
        self.timeSeriesCatFileLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.timeSeriesCatFileLabel.setText("")
        self.timeSeriesCatFileLabel.setObjectName("timeSeriesCatFileLabel")
        self.horizontalLayout_33.addWidget(self.timeSeriesCatFileLabel)
        self.verticalLayout_23.addLayout(self.horizontalLayout_33)
        self.timeSeriesCatCsvTabWidget = QtWidgets.QTabWidget(self.verticalLayoutWidget)
        self.timeSeriesCatCsvTabWidget.setObjectName("timeSeriesCatCsvTabWidget")
        self.timeSeriesCatRawTab = QtWidgets.QWidget()
        self.timeSeriesCatRawTab.setObjectName("timeSeriesCatRawTab")
        self.verticalLayout_29 = QtWidgets.QVBoxLayout(self.timeSeriesCatRawTab)
        self.verticalLayout_29.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_29.setObjectName("verticalLayout_29")
        self.scrollArea = QtWidgets.QScrollArea(self.timeSeriesCatRawTab)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 228, 356))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_30 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_30.setObjectName("verticalLayout_30")
        self.rawTableWidget = QtWidgets.QTableWidget(self.scrollAreaWidgetContents)
        self.rawTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.rawTableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.rawTableWidget.setObjectName("rawTableWidget")
        self.rawTableWidget.setColumnCount(0)
        self.rawTableWidget.setRowCount(0)
        self.rawTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_30.addWidget(self.rawTableWidget)
        self.groupBox_10 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_10.setObjectName("groupBox_10")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_10)
        self.gridLayout.setObjectName("gridLayout")
        self.rawMatlabRadioButton = QtWidgets.QRadioButton(self.groupBox_10)
        self.rawMatlabRadioButton.setObjectName("rawMatlabRadioButton")
        self.gridLayout.addWidget(self.rawMatlabRadioButton, 1, 0, 1, 1)
        self.rawIgorRadioButton = QtWidgets.QRadioButton(self.groupBox_10)
        self.rawIgorRadioButton.setObjectName("rawIgorRadioButton")
        self.gridLayout.addWidget(self.rawIgorRadioButton, 0, 1, 1, 1)
        self.rawExcelRadioButton = QtWidgets.QRadioButton(self.groupBox_10)
        self.rawExcelRadioButton.setObjectName("rawExcelRadioButton")
        self.gridLayout.addWidget(self.rawExcelRadioButton, 1, 1, 1, 1)
        self.rawIsoRadioButton = QtWidgets.QRadioButton(self.groupBox_10)
        self.rawIsoRadioButton.setChecked(True)
        self.rawIsoRadioButton.setObjectName("rawIsoRadioButton")
        self.gridLayout.addWidget(self.rawIsoRadioButton, 0, 0, 1, 1)
        self.rawCustomRadioButton = QtWidgets.QRadioButton(self.groupBox_10)
        self.rawCustomRadioButton.setObjectName("rawCustomRadioButton")
        self.gridLayout.addWidget(self.rawCustomRadioButton, 2, 0, 1, 1)
        self.rawCustomLineEdit = QtWidgets.QLineEdit(self.groupBox_10)
        self.rawCustomLineEdit.setObjectName("rawCustomLineEdit")
        self.gridLayout.addWidget(self.rawCustomLineEdit, 2, 1, 1, 1)
        self.verticalLayout_30.addWidget(self.groupBox_10)
        self.formLayout_11 = QtWidgets.QFormLayout()
        self.formLayout_11.setObjectName("formLayout_11")
        self.label_30 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_30.setObjectName("label_30")
        self.formLayout_11.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_30)
        self.rawTimeColumnLabel = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.rawTimeColumnLabel.setObjectName("rawTimeColumnLabel")
        self.formLayout_11.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.rawTimeColumnLabel)
        self.rawTimeColumnSpinBox = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.rawTimeColumnSpinBox.setMinimum(1)
        self.rawTimeColumnSpinBox.setObjectName("rawTimeColumnSpinBox")
        self.formLayout_11.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.rawTimeColumnSpinBox)
        self.rawFirstIonColumnLabel = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.rawFirstIonColumnLabel.setObjectName("rawFirstIonColumnLabel")
        self.formLayout_11.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.rawFirstIonColumnLabel)
        self.rawFirstIonColumnLineEdit = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.rawFirstIonColumnLineEdit.setMinimum(2)
        self.rawFirstIonColumnLineEdit.setMaximum(99999)
        self.rawFirstIonColumnLineEdit.setObjectName("rawFirstIonColumnLineEdit")
        self.formLayout_11.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.rawFirstIonColumnLineEdit)
        self.rawIonRowLabel = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.rawIonRowLabel.setObjectName("rawIonRowLabel")
        self.formLayout_11.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.rawIonRowLabel)
        self.rawIonRowLineEdit = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.rawIonRowLineEdit.setMinimum(1)
        self.rawIonRowLineEdit.setMaximum(99999)
        self.rawIonRowLineEdit.setObjectName("rawIonRowLineEdit")
        self.formLayout_11.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.rawIonRowLineEdit)
        self.verticalLayout_30.addLayout(self.formLayout_11)
        self.rawFinishPushButton = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.rawFinishPushButton.setObjectName("rawFinishPushButton")
        self.verticalLayout_30.addWidget(self.rawFinishPushButton)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_29.addWidget(self.scrollArea)
        self.timeSeriesCatCsvTabWidget.addTab(self.timeSeriesCatRawTab, "")
        self.timeSeriesCatProcessedTab = QtWidgets.QWidget()
        self.timeSeriesCatProcessedTab.setObjectName("timeSeriesCatProcessedTab")
        self.verticalLayout_28 = QtWidgets.QVBoxLayout(self.timeSeriesCatProcessedTab)
        self.verticalLayout_28.setObjectName("verticalLayout_28")
        self.processedTableWidget = QtWidgets.QTableWidget(self.timeSeriesCatProcessedTab)
        self.processedTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.processedTableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.processedTableWidget.setObjectName("processedTableWidget")
        self.processedTableWidget.setColumnCount(1)
        self.processedTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.processedTableWidget.setHorizontalHeaderItem(0, item)
        self.processedTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_28.addWidget(self.processedTableWidget)
        self.timeSeriesCatCsvTabWidget.addTab(self.timeSeriesCatProcessedTab, "")
        self.verticalLayout_23.addWidget(self.timeSeriesCatCsvTabWidget)
        self.horizontalLayout_28 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")
        self.label_16 = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_16.setObjectName("label_16")
        self.horizontalLayout_28.addWidget(self.label_16)
        self.rtolDoubleSpinBox = QtWidgets.QDoubleSpinBox(self.verticalLayoutWidget)
        self.rtolDoubleSpinBox.setMinimum(0.01)
        self.rtolDoubleSpinBox.setMaximum(9.99)
        self.rtolDoubleSpinBox.setProperty("value", 1.0)
        self.rtolDoubleSpinBox.setObjectName("rtolDoubleSpinBox")
        self.horizontalLayout_28.addWidget(self.rtolDoubleSpinBox)
        self.verticalLayout_23.addLayout(self.horizontalLayout_28)
        self.catPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.catPushButton.setObjectName("catPushButton")
        self.verticalLayout_23.addWidget(self.catPushButton)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.timeSeriesCatSplitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_25 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_25.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_25.setObjectName("verticalLayout_25")
        self.timeSeriesesTableWidget = QtWidgets.QTableWidget(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timeSeriesesTableWidget.sizePolicy().hasHeightForWidth())
        self.timeSeriesesTableWidget.setSizePolicy(sizePolicy)
        self.timeSeriesesTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.timeSeriesesTableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.timeSeriesesTableWidget.setObjectName("timeSeriesesTableWidget")
        self.timeSeriesesTableWidget.setColumnCount(2)
        self.timeSeriesesTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.timeSeriesesTableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.timeSeriesesTableWidget.setHorizontalHeaderItem(1, item)
        self.timeSeriesesTableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.timeSeriesesTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_25.addWidget(self.timeSeriesesTableWidget)
        self.horizontalLayout_29 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.label_17 = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_17.sizePolicy().hasHeightForWidth())
        self.label_17.setSizePolicy(sizePolicy)
        self.label_17.setObjectName("label_17")
        self.horizontalLayout_29.addWidget(self.label_17)
        self.rmSelectedPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rmSelectedPushButton.sizePolicy().hasHeightForWidth())
        self.rmSelectedPushButton.setSizePolicy(sizePolicy)
        self.rmSelectedPushButton.setObjectName("rmSelectedPushButton")
        self.horizontalLayout_29.addWidget(self.rmSelectedPushButton)
        self.rmAllPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rmAllPushButton.sizePolicy().hasHeightForWidth())
        self.rmAllPushButton.setSizePolicy(sizePolicy)
        self.rmAllPushButton.setObjectName("rmAllPushButton")
        self.horizontalLayout_29.addWidget(self.rmAllPushButton)
        self.verticalLayout_25.addLayout(self.horizontalLayout_29)
        self.horizontalLayout_31 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_31.setObjectName("horizontalLayout_31")
        self.label_26 = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_26.sizePolicy().hasHeightForWidth())
        self.label_26.setSizePolicy(sizePolicy)
        self.label_26.setObjectName("label_26")
        self.horizontalLayout_31.addWidget(self.label_26)
        self.intSelectedPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.intSelectedPushButton.sizePolicy().hasHeightForWidth())
        self.intSelectedPushButton.setSizePolicy(sizePolicy)
        self.intSelectedPushButton.setObjectName("intSelectedPushButton")
        self.horizontalLayout_31.addWidget(self.intSelectedPushButton)
        self.intAllPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.intAllPushButton.sizePolicy().hasHeightForWidth())
        self.intAllPushButton.setSizePolicy(sizePolicy)
        self.intAllPushButton.setObjectName("intAllPushButton")
        self.horizontalLayout_31.addWidget(self.intAllPushButton)
        self.verticalLayout_25.addLayout(self.horizontalLayout_31)
        self.timeSeriesTableWidget = QtWidgets.QTableWidget(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timeSeriesTableWidget.sizePolicy().hasHeightForWidth())
        self.timeSeriesTableWidget.setSizePolicy(sizePolicy)
        self.timeSeriesTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.timeSeriesTableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.timeSeriesTableWidget.setObjectName("timeSeriesTableWidget")
        self.timeSeriesTableWidget.setColumnCount(2)
        self.timeSeriesTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.timeSeriesTableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.timeSeriesTableWidget.setHorizontalHeaderItem(1, item)
        self.timeSeriesTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_25.addWidget(self.timeSeriesTableWidget)
        self.exportPushButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.exportPushButton.sizePolicy().hasHeightForWidth())
        self.exportPushButton.setSizePolicy(sizePolicy)
        self.exportPushButton.setObjectName("exportPushButton")
        self.verticalLayout_25.addWidget(self.exportPushButton)
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.timeSeriesCatSplitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_26 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_26.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_26.setObjectName("verticalLayout_26")
        self.widget = QtWidgets.QWidget(self.verticalLayoutWidget_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.verticalLayout_26.addWidget(self.widget)
        self.horizontalLayout_32 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_32.setObjectName("horizontalLayout_32")
        self.showLegendsCheckBox = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showLegendsCheckBox.sizePolicy().hasHeightForWidth())
        self.showLegendsCheckBox.setSizePolicy(sizePolicy)
        self.showLegendsCheckBox.setObjectName("showLegendsCheckBox")
        self.horizontalLayout_32.addWidget(self.showLegendsCheckBox)
        self.logScaleCheckBox = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logScaleCheckBox.sizePolicy().hasHeightForWidth())
        self.logScaleCheckBox.setSizePolicy(sizePolicy)
        self.logScaleCheckBox.setObjectName("logScaleCheckBox")
        self.horizontalLayout_32.addWidget(self.logScaleCheckBox)
        self.rescalePushButton = QtWidgets.QPushButton(self.verticalLayoutWidget_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rescalePushButton.sizePolicy().hasHeightForWidth())
        self.rescalePushButton.setSizePolicy(sizePolicy)
        self.rescalePushButton.setObjectName("rescalePushButton")
        self.horizontalLayout_32.addWidget(self.rescalePushButton)
        self.verticalLayout_26.addLayout(self.horizontalLayout_32)
        self.verticalLayout.addWidget(self.timeSeriesCatSplitter)

        self.retranslateUi(Form)
        self.timeSeriesCatCsvTabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.csvAddPushButton.setText(_translate("Form", "Add csv files"))
        self.label_31.setText(_translate("Form", "File:"))
        self.groupBox_10.setTitle(_translate("Form", "time format"))
        self.rawMatlabRadioButton.setText(_translate("Form", "matlab"))
        self.rawIgorRadioButton.setText(_translate("Form", "igor time"))
        self.rawExcelRadioButton.setText(_translate("Form", "excel time"))
        self.rawIsoRadioButton.setText(_translate("Form", "iso time"))
        self.rawCustomRadioButton.setText(_translate("Form", "custom"))
        self.rawCustomLineEdit.setText(_translate("Form", "%Y%m%d %H:%M:%S"))
        self.label_30.setText(_translate("Form", "Key row/col"))
        self.rawTimeColumnLabel.setText(_translate("Form", "Time column"))
        self.rawFirstIonColumnLabel.setText(_translate("Form", "First ion column"))
        self.rawIonRowLabel.setText(_translate("Form", "Ion row"))
        self.rawFinishPushButton.setText(_translate("Form", "Finish"))
        self.timeSeriesCatCsvTabWidget.setTabText(self.timeSeriesCatCsvTabWidget.indexOf(self.timeSeriesCatRawTab), _translate("Form", "raw data"))
        item = self.processedTableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "time"))
        self.timeSeriesCatCsvTabWidget.setTabText(self.timeSeriesCatCsvTabWidget.indexOf(self.timeSeriesCatProcessedTab), _translate("Form", "processed"))
        self.label_16.setText(_translate("Form", "rtol"))
        self.catPushButton.setText(_translate("Form", "Concatenate/Next file"))
        item = self.timeSeriesesTableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "tag"))
        item = self.timeSeriesesTableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "mz"))
        self.label_17.setText(_translate("Form", "Remove"))
        self.rmSelectedPushButton.setText(_translate("Form", "selected"))
        self.rmAllPushButton.setText(_translate("Form", "all"))
        self.label_26.setText(_translate("Form", "interpolate"))
        self.intSelectedPushButton.setText(_translate("Form", "selected"))
        self.intAllPushButton.setText(_translate("Form", "all"))
        item = self.timeSeriesTableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "time"))
        item = self.timeSeriesTableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "intensity"))
        self.exportPushButton.setText(_translate("Form", "Export all time series"))
        self.showLegendsCheckBox.setText(_translate("Form", "show legends"))
        self.logScaleCheckBox.setText(_translate("Form", "y-log scale"))
        self.rescalePushButton.setText(_translate("Form", "autoscale y axis"))

