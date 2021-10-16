from datetime import datetime, timedelta
import numpy as np

def getIsoTime(dt: datetime):
    return dt.isoformat()

def fromIsoTime(s: str)->datetime:
    return datetime.fromisoformat(s).replace(tzinfo=None) # py 3.7

igorTimeStandard = datetime(1904, 1, 1)

def getIgorTime(dt: datetime):
    return int((dt - igorTimeStandard).total_seconds())

def fromIgorTime(t: int):
    return igorTimeStandard+timedelta(seconds=t)

matlabTimeStandard = np.float64(-719529).astype('M8[D]')

def getMatlabTime(dt: datetime):
    return (np.datetime64(dt) - matlabTimeStandard).astype('m8[s]').astype(float) / 86400.

def fromMatlabTime(t: float):
    return (matlabTimeStandard+np.float_(t*86400).astype('m8[s]')).astype(datetime)

excelTimeStandard = datetime(1899, 12, 31)

def getExcelTime(dt: datetime):
    return (dt - excelTimeStandard).total_seconds() / 86400.

def fromExcelTime(t: float):
    return excelTimeStandard+timedelta(seconds=t*86400)

def getTimesExactToS(dt: datetime):
    dt = dt.replace(microsecond=0)
    return [getIsoTime(dt), getIgorTime(dt), getMatlabTime(dt), getExcelTime(dt)]

__all__ = [s for s in locals() if s.find('get')==0 or s.find('from')==0]
