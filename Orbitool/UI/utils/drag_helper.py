from pathlib import Path
from PyQt5.QtCore import QMimeData
from typing import Iterable, Literal 


class DragHelper:
    def __init__(self, accepts: Iterable[Literal["file", "image", "text"]]) -> None:
        accepts = set(accepts)
        self.file_ok = "file" in accepts
        self.image_ok = "image" in accepts
        self.text_ok = "text" in accepts

    def accept(self, data: QMimeData):
        if data.hasUrls(): # file is not text
            if self.image_ok and data.hasImage():
                return True
            if self.file_ok and data.hasUrls():
                for url in data.urls():
                    if url.isLocalFile():
                        return True 
        elif self.text_ok and data.hasText():
            return True
        return False

    def yield_file(self, data: QMimeData):
        if data.hasUrls():
            for url in data.urls():
                if url.isLocalFile():
                    yield Path(url.toLocalFile())

    def get_text(self, data: QMimeData):
        if data.hasUrls():
            return ""
        if data.hasText():
            return data.text()
        return ""

    