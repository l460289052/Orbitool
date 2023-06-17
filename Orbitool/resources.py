from .config import RESOURCE_PATH, setting

ICON_PATH = RESOURCE_PATH / "icons"

class _IconGetter:
    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, ins, own):
        from PyQt6.QtGui import QIcon, QPixmap, QImage
        from PyQt6.QtWidgets import QApplication
        from PyQt6 import QtCore
        img = QImage(str(ICON_PATH / self.name))
        app: QApplication = setting.get_global_var("app")
        if app.styleHints().colorScheme() == QtCore.Qt.ColorScheme.Dark:
            img.invertPixels()
        return QIcon(QPixmap.fromImage(img))

class _Icons:
    SpectrumIcon = _IconGetter("spectrum.png")
    MeanIcon = _IconGetter("mean.png")

Icons = _Icons()

