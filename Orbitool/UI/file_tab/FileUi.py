# Form implementation generated from reading ui file 'Orbitool\UI\file_tab\File.ui'
#
# Created by: PyQt6 UI code generator 6.5.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(699, 479)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.addFilePushButton = QtWidgets.QPushButton(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addFilePushButton.sizePolicy().hasHeightForWidth())
        self.addFilePushButton.setSizePolicy(sizePolicy)
        self.addFilePushButton.setObjectName("addFilePushButton")
        self.verticalLayout_5.addWidget(self.addFilePushButton)
        self.addFolderPushButton = QtWidgets.QPushButton(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addFolderPushButton.sizePolicy().hasHeightForWidth())
        self.addFolderPushButton.setSizePolicy(sizePolicy)
        self.addFolderPushButton.setObjectName("addFolderPushButton")
        self.verticalLayout_5.addWidget(self.addFolderPushButton)
        self.recursionCheckBox = QtWidgets.QCheckBox(parent=Form)
        self.recursionCheckBox.setChecked(True)
        self.recursionCheckBox.setObjectName("recursionCheckBox")
        self.verticalLayout_5.addWidget(self.recursionCheckBox)
        spacerItem = QtWidgets.QSpacerItem(20, 15, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout_5.addItem(spacerItem)
        self.removeFilePushButton = QtWidgets.QPushButton(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.removeFilePushButton.sizePolicy().hasHeightForWidth())
        self.removeFilePushButton.setSizePolicy(sizePolicy)
        self.removeFilePushButton.setObjectName("removeFilePushButton")
        self.verticalLayout_5.addWidget(self.removeFilePushButton)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_5.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout_5)
        self.tableWidget = QtWidgets.QTableWidget(parent=Form)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setDragEnabled(True)
        self.tableWidget.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DropOnly)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)
        self.tableWidget.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)
        self.tableWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        self.tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.horizontalLayout.addWidget(self.tableWidget)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.formLayout_10 = QtWidgets.QFormLayout()
        self.formLayout_10.setObjectName("formLayout_10")
        self.groupBox = QtWidgets.QGroupBox(parent=Form)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.label_7 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_7)
        self.startDateTimeEdit = QtWidgets.QDateTimeEdit(parent=self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.startDateTimeEdit.sizePolicy().hasHeightForWidth())
        self.startDateTimeEdit.setSizePolicy(sizePolicy)
        self.startDateTimeEdit.setMaximumDateTime(QtCore.QDateTime(QtCore.QDate(9999, 12, 31), QtCore.QTime(23, 59, 59)))
        self.startDateTimeEdit.setObjectName("startDateTimeEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.startDateTimeEdit)
        self.label_8 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_8)
        self.endDateTimeEdit = QtWidgets.QDateTimeEdit(parent=self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.endDateTimeEdit.sizePolicy().hasHeightForWidth())
        self.endDateTimeEdit.setSizePolicy(sizePolicy)
        self.endDateTimeEdit.setObjectName("endDateTimeEdit")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.endDateTimeEdit)
        self.autoTimeCheckBox = QtWidgets.QCheckBox(parent=self.groupBox)
        self.autoTimeCheckBox.setChecked(True)
        self.autoTimeCheckBox.setObjectName("autoTimeCheckBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.autoTimeCheckBox)
        self.timeAdjustPushButton = QtWidgets.QPushButton(parent=self.groupBox)
        self.timeAdjustPushButton.setObjectName("timeAdjustPushButton")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.timeAdjustPushButton)
        self.formLayout_10.setWidget(0, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.groupBox)
        self.groupBox_5 = QtWidgets.QGroupBox(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_5)
        self.gridLayout.setContentsMargins(0, 9, 0, 0)
        self.gridLayout.setHorizontalSpacing(3)
        self.gridLayout.setObjectName("gridLayout")
        self.nSpectraRadioButton = QtWidgets.QRadioButton(parent=self.groupBox_5)
        self.nSpectraRadioButton.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nSpectraRadioButton.sizePolicy().hasHeightForWidth())
        self.nSpectraRadioButton.setSizePolicy(sizePolicy)
        self.nSpectraRadioButton.setChecked(False)
        self.nSpectraRadioButton.setObjectName("nSpectraRadioButton")
        self.gridLayout.addWidget(self.nSpectraRadioButton, 0, 0, 1, 1)
        self.periodToolButton = QtWidgets.QToolButton(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.periodToolButton.sizePolicy().hasHeightForWidth())
        self.periodToolButton.setSizePolicy(sizePolicy)
        self.periodToolButton.setObjectName("periodToolButton")
        self.gridLayout.addWidget(self.periodToolButton, 2, 1, 1, 1)
        self.nMinutesRadioButton = QtWidgets.QRadioButton(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nMinutesRadioButton.sizePolicy().hasHeightForWidth())
        self.nMinutesRadioButton.setSizePolicy(sizePolicy)
        self.nMinutesRadioButton.setChecked(True)
        self.nMinutesRadioButton.setObjectName("nMinutesRadioButton")
        self.gridLayout.addWidget(self.nMinutesRadioButton, 1, 0, 1, 1)
        self.nSpectraSpinBox = QtWidgets.QSpinBox(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nSpectraSpinBox.sizePolicy().hasHeightForWidth())
        self.nSpectraSpinBox.setSizePolicy(sizePolicy)
        self.nSpectraSpinBox.setMaximumSize(QtCore.QSize(16777215, 18))
        self.nSpectraSpinBox.setMinimum(1)
        self.nSpectraSpinBox.setMaximum(9999)
        self.nSpectraSpinBox.setProperty("value", 10)
        self.nSpectraSpinBox.setObjectName("nSpectraSpinBox")
        self.gridLayout.addWidget(self.nSpectraSpinBox, 0, 1, 1, 1)
        self.periodRadioButton = QtWidgets.QRadioButton(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.periodRadioButton.sizePolicy().hasHeightForWidth())
        self.periodRadioButton.setSizePolicy(sizePolicy)
        self.periodRadioButton.setText("")
        self.periodRadioButton.setChecked(False)
        self.periodRadioButton.setObjectName("periodRadioButton")
        self.gridLayout.addWidget(self.periodRadioButton, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 2, 1, 1)
        self.nMinutesLineEdit = QtWidgets.QLineEdit(parent=self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nMinutesLineEdit.sizePolicy().hasHeightForWidth())
        self.nMinutesLineEdit.setSizePolicy(sizePolicy)
        self.nMinutesLineEdit.setObjectName("nMinutesLineEdit")
        self.gridLayout.addWidget(self.nMinutesLineEdit, 1, 1, 1, 2)
        self.formLayout_10.setWidget(1, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.groupBox_5)
        self.line = QtWidgets.QFrame(parent=Form)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.formLayout_10.setWidget(2, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.line)
        self.rtolLabel = QtWidgets.QLabel(parent=Form)
        self.rtolLabel.setObjectName("rtolLabel")
        self.formLayout_10.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.rtolLabel)
        self.rtolDoubleSpinBox = QtWidgets.QDoubleSpinBox(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rtolDoubleSpinBox.sizePolicy().hasHeightForWidth())
        self.rtolDoubleSpinBox.setSizePolicy(sizePolicy)
        self.rtolDoubleSpinBox.setMinimum(0.01)
        self.rtolDoubleSpinBox.setMaximum(99.99)
        self.rtolDoubleSpinBox.setSingleStep(0.5)
        self.rtolDoubleSpinBox.setProperty("value", 1.0)
        self.rtolDoubleSpinBox.setObjectName("rtolDoubleSpinBox")
        self.formLayout_10.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.rtolDoubleSpinBox)
        self.groupBox_6 = QtWidgets.QGroupBox(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy)
        self.groupBox_6.setObjectName("groupBox_6")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox_6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.positiveRadioButton = QtWidgets.QRadioButton(parent=self.groupBox_6)
        self.positiveRadioButton.setObjectName("positiveRadioButton")
        self.horizontalLayout_2.addWidget(self.positiveRadioButton)
        self.negativeRadioButton = QtWidgets.QRadioButton(parent=self.groupBox_6)
        self.negativeRadioButton.setChecked(True)
        self.negativeRadioButton.setObjectName("negativeRadioButton")
        self.horizontalLayout_2.addWidget(self.negativeRadioButton)
        self.formLayout_10.setWidget(4, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.groupBox_6)
        self.verticalLayout_6.addLayout(self.formLayout_10)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_6.addItem(spacerItem2)
        self.averageCheckBox = QtWidgets.QCheckBox(parent=Form)
        self.averageCheckBox.setChecked(True)
        self.averageCheckBox.setObjectName("averageCheckBox")
        self.verticalLayout_6.addWidget(self.averageCheckBox)
        self.label_2 = QtWidgets.QLabel(parent=Form)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_6.addWidget(self.label_2)
        self.selectedPushButton = QtWidgets.QPushButton(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectedPushButton.sizePolicy().hasHeightForWidth())
        self.selectedPushButton.setSizePolicy(sizePolicy)
        self.selectedPushButton.setObjectName("selectedPushButton")
        self.verticalLayout_6.addWidget(self.selectedPushButton)
        self.allPushButton = QtWidgets.QPushButton(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.allPushButton.sizePolicy().hasHeightForWidth())
        self.allPushButton.setSizePolicy(sizePolicy)
        self.allPushButton.setObjectName("allPushButton")
        self.verticalLayout_6.addWidget(self.allPushButton)
        self.horizontalLayout.addLayout(self.verticalLayout_6)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.addFilePushButton.setToolTip(_translate("Form", "Alt+I"))
        self.addFilePushButton.setText(_translate("Form", "&Import file(s)"))
        self.addFilePushButton.setShortcut(_translate("Form", "Alt+I"))
        self.addFolderPushButton.setToolTip(_translate("Form", "Alt+F"))
        self.addFolderPushButton.setText(_translate("Form", "Import &folder"))
        self.addFolderPushButton.setShortcut(_translate("Form", "Alt+F"))
        self.recursionCheckBox.setText(_translate("Form", "Subdirectory"))
        self.removeFilePushButton.setToolTip(_translate("Form", "Del Key"))
        self.removeFilePushButton.setText(_translate("Form", "Remove selected"))
        self.removeFilePushButton.setShortcut(_translate("Form", "Del"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Name"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Start time"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "End time"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Scan num"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Path"))
        self.groupBox.setTitle(_translate("Form", "Average time range"))
        self.label_7.setText(_translate("Form", "from"))
        self.startDateTimeEdit.setDisplayFormat(_translate("Form", "yyyy/M/d H:mm:ss"))
        self.label_8.setText(_translate("Form", "to"))
        self.endDateTimeEdit.setDisplayFormat(_translate("Form", "yyyy/M/d H:mm:ss"))
        self.autoTimeCheckBox.setText(_translate("Form", "auto"))
        self.timeAdjustPushButton.setText(_translate("Form", "adjust to selected files"))
        self.groupBox_5.setTitle(_translate("Form", "Average according to"))
        self.nSpectraRadioButton.setText(_translate("Form", "every"))
        self.periodToolButton.setText(_translate("Form", "custom"))
        self.nMinutesRadioButton.setText(_translate("Form", "every"))
        self.label.setText(_translate("Form", "spectra"))
        self.label_4.setText(_translate("Form", "periods"))
        self.nMinutesLineEdit.setToolTip(_translate("Form", "1000s ( 1000 seconds )\n"
"10m5s ( 10 minutes and 5 seconds )\n"
"1h ( 1 hour )"))
        self.nMinutesLineEdit.setText(_translate("Form", "2h5m"))
        self.nMinutesLineEdit.setPlaceholderText(_translate("Form", "2h5m"))
        self.rtolLabel.setToolTip(_translate("Form", "tolerance(ppm)"))
        self.rtolLabel.setText(_translate("Form", "tolerance(ppm)"))
        self.groupBox_6.setTitle(_translate("Form", "Polarity"))
        self.positiveRadioButton.setText(_translate("Form", "&Positive"))
        self.negativeRadioButton.setText(_translate("Form", "&Negative"))
        self.averageCheckBox.setText(_translate("Form", "Average"))
        self.label_2.setText(_translate("Form", "Show spectra for"))
        self.selectedPushButton.setToolTip(_translate("Form", "Alt+S"))
        self.selectedPushButton.setText(_translate("Form", "&Selected file(s)"))
        self.selectedPushButton.setShortcut(_translate("Form", "Alt+S"))
        self.allPushButton.setToolTip(_translate("Form", "Return Key"))
        self.allPushButton.setText(_translate("Form", "&All file(s)"))
        self.allPushButton.setShortcut(_translate("Form", "Return"))
