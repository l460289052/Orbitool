from .config import RESOURCE_PATH

ICON_PATH = RESOURCE_PATH / "icons"

class _IconGetter:
    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, ins, own):
        from PyQt6.QtGui import QIcon
        return QIcon(str(ICON_PATH / self.name))

class _Icons:
    SpectrumIcon = _IconGetter("spectrum.png")
    MeanIcon = _IconGetter("mean.png")

Icons = _Icons()

