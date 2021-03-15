import multiprocessing
import os
from datetime import datetime, timedelta

import pytest

from ... import files


def test_FileTraveler_noRecurrent():
    ft = files.FolderTraveler(".", '.py', False)
    thisFile=os.path.split(__file__)[1]
    find = False
    for f in ft:
        if os.path.split(f)[1] == thisFile:
            find = True
    assert not find


def test_FileTraveler_recurrent():
    ft = files.FolderTraveler(".", '.py', True)
    thisFile=os.path.split(__file__)[1]
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


class TestFileList:
    def setup_class(self):
        self.lf = files.FileList()
        self.ref = datetime.now()
        for i in range(10):
            self.lf.addFile(TenMinuteFile(self.ref + timedelta(minutes=15) * i))

    def test_add(self):
        with pytest.raises(ValueError):
            self.lf.addFile(TenMinuteFile(self.ref + timedelta(minutes=5)))
    
    def test_timeRange(self):
        assert self.lf.timeRange() == (self.ref, self.ref+timedelta(minutes=15*9+10))








    
    
    
    
