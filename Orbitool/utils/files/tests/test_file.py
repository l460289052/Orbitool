import multiprocessing
import os
from datetime import datetime, timedelta

import pytest

from ... import files


def test_FileTraveler_noRecurrent():
    ft = files.FolderTraveler(".", '.py', False)
    thisFile = os.path.split(__file__)[1]
    find = False
    for f in ft:
        if os.path.split(f)[1] == thisFile:
            find = True
    assert not find


def test_FileTraveler_recurrent():
    ft = files.FolderTraveler(".", '.py', True)
    thisFile = os.path.split(__file__)[1]
    find = False
    for f in ft:
        if os.path.split(f)[1] == thisFile:
            find = True
    assert find


class TenMinuteFile(files.File):
    def __init__(self, creationDatetime: datetime):
        self.path = datetime.now()
        self.creationDatetime = creationDatetime
        self.startTimedelta = timedelta()
        self.endTimedelta = timedelta(minutes=10)
