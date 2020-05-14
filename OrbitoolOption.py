# -*- coding: utf-8 -*-
from typing import Union, List

from PyQt5.QtWidgets import QAbstractButton, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QLineEdit, QSlider


class Option:
    def __init__(self):
        self.buttons = {}
        self.spinBoxes = {}
        self.dateTimeEdits = {}
        self.lineEdits = {}
        self.sliders = {}

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
        elif isinstance(o, QSlider):
            self.sliders[name] = o.value()
        else:
            raise TypeError()

    def addWidgets(self, window, names: List[str]):
        for name in names:
            self.addWidget(window, name)

    def addAllWidgets(self, window):
        for k, v in window.__dict__.items():
            try:
                self.addWidget(window, k)
            except TypeError:
                pass

    def applyWidgets(self, window):
        for k, v in self.buttons.items():
            try:
                getattr(window, k).setChecked(v)
            except AttributeError:
                pass
        for k, v in self.spinBoxes.items():
            try:
                getattr(window, k).setValue(v)
            except AttributeError:
                pass
        for k, v in self.dateTimeEdits.items():
            try:
                getattr(window, k).setDateTime(v)
            except AttributeError:
                pass
        for k, v in self.lineEdits.items():
            try:
                getattr(window, k).setText(v)
            except AttributeError:
                pass
        for k, v in self.sliders.items():
            try:
                getattr(window, k).setValue(v)
            except AttributeError:
                pass

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
