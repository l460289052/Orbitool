from datetime import datetime, timedelta

class File:
    def __init__(self):
        self.path: str = None
        self.creationDatetime: datetime = None
        self.startTimedelta: timedelta = None
        self.endTimedelta: timedelta = None

    @property
    def startDatetime(self) -> datetime:
        return self.creationDatetime + self.startTimedelta
        
    @property
    def endDatetime(self) -> datetime:
        return self.creationDatetime + self.endTimedelta

    def __str__(self):
        return f"self.path creationDatetime {self.creationDatetime.isoformat()}"