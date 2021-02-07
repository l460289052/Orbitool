from typing import Iterable
from warnings import warn


class iterator:
    def __init__(self, l: Iterable[object]) -> None:
        self._iter = iter(l)
        try:
            self.value: object = next(self._iter)
            self.end = False
        except StopIteration:
            self.value = None
            self.end = True
        self.index = 0

    def next(self):
        """
        deprecated
        """
        warn('deprecated', DeprecationWarning)
        self.inc()

    def inc(self):
        if not self.end:
            try:
                self.value = next(self._iter)
            except StopIteration:
                self.value = None
                self.end = True
            self.index += 1
            return self.value
        return None
