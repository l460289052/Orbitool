# -*- coding: utf-8 -*-
from typing import Union, List

from PyQt5.QtWidgets import QAbstractButton, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QLineEdit

class Option:
	def __init__(self):
		self.buttons = {}
		self.spinBoxes = {}
		self.dateTimeEdits = {}
		self.lineEdits = {}

		self.objects = {}

	def addWidget(self, window, name):
		o = getattr(window, name)
		if isinstance(o, QAbstractButton):
			self.buttons[name] = o.isChecked()
		elif isinstance(o, (QSpinBox, QDoubleSpinBox)):
			self.spinBoxes[name] = o.value()
		elif isinstance(o, QDateTimeEdit):
			self.dateTimeEdits[name] = o.dateTime().toPyDateTime()
		elif isinstance(o, QLineEdit):
			self.lineEdits[name] = o.text()
		else:
			raise TypeError()

	def addWidgets(self, window, names: List[str]):
		for name in names:
			self.addWidget(window, name)

	def applyWidgets(self, window):
		for k, v in self.buttons.items():
			getattr(window, k).setChecked(v)
		for k, v in self.spinBoxes.items():
			getattr(window, k).setValue(v)
		for k, v in self.dateTimeEdits.items():
			getattr(window, k).setDateTime(v)
		for k, v in self.lineEdits.items():
			getattr(window, k).setText(v)
			

	def addObject(self, window, name):
		o = getattr(window, name)
		self.objects[name] = name
	
	def addObjects(self, window, names):
		for name in names:
			o = getattr(window, name)
			self.objects[name] = o

	def applyObjects(self, window):
		for k, v in self.objects.items():
			setattr(window, k, v)