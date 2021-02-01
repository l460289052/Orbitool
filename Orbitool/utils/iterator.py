from typing import Iterable


class iterator:
    def __init__(self, l: Iterable) -> None:
        self._iter = iter(l)
        try:
            self.value = next(self._iter)
            self.end = False
        except StopIteration:
            self.value = None
            self.end = True
        self.index = 0

    def next(self):
        if not self.end:
            try:
                self.value = next(self._iter)
            except StopIteration:
                self.value = None
                self.end = True
            self.index += 1
