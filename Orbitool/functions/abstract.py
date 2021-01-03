from datetime import datetime
from typing import List, Iterable, Tuple
import multiprocessing
import traceback

def nullSendStatus(fileTime: datetime, msg: str, index: int, length: int):
    pass


def processWithTime(func, fileTime, args, signalQueue):
    result = None
    try:
        result = func(fileTime, *args)
    except Exception as e:
        with open('error.txt', 'a') as file:
            print('', datetime.now, str(e), sep='\n', file=file)
            traceback.print_exc(file=file)
            print(str(e))
            traceback.print_exc()
    signalQueue.put(fileTime)
    return result


def processWithoutTime(func, args, signalQueue):
    result = None
    try:
        result = func(*args)
    except Exception as e:
        with open('error.txt', 'a') as file:
            print('', datetime.now, str(e), sep='\n', file=file)
            traceback.print_exc(file=file)
            print(str(e))
            traceback.print_exc()
    signalQueue.put(True)
    return result


def multiProcess(func, argsList: List[Tuple], fileTime, cpu=None, sendStatusFunc=nullSendStatus):
    '''
    multi process
    the first line of func.__doc__ will be shown message
    if fileTime is a list, func's first arguement must be fileTime
    '''
    if isinstance(fileTime, Iterable):
        if len(argsList) != len(fileTime):
            raise ValueError('len(fileTime)!=len(argsList)')
    if cpu is None or cpu >= multiprocessing.cpu_count():
        cpu = multiprocessing.cpu_count() - 1
    if cpu <= 0:
        cpu = 1
    msg = ''
    if func.__doc__ is not None:
        for line in func.__doc__.splitlines():
            strip = line.strip()
            if len(strip) > 0:
                msg = strip
                break
    length = len(argsList)
    if cpu == 1:
        results = []
        if isinstance(fileTime, Iterable):
            for i, args in enumerate(argsList):
                sendStatusFunc(fileTime[i], msg, i, length)
                results.append(func(fileTime[i], *args))
            sendStatusFunc(fileTime[-1], msg, length, length)
        else:
            for i, args in enumerate(argsList):
                sendStatusFunc(fileTime, msg, i, length)
                results.append(func(*args))
            sendStatusFunc(fileTime, msg, length, length)
        return results
    else:
        with multiprocessing.Manager() as manager:
            queue = manager.Queue()
            with multiprocessing.Pool(cpu) as pool:
                if isinstance(fileTime, Iterable):
                    results: multiprocessing.pool.MapResult = pool.starmap_async(
                        processWithTime, [(func, time, args, queue) for time, args in zip(fileTime, argsList)])
                    pool.close()
                    sendStatusFunc(fileTime[0], msg, 0, length)
                    for i in range(length):
                        time = queue.get()
                        sendStatusFunc(time, msg, i, length)
                    return results.get()
                else:
                    results: multiprocessing.pool.MapResult = pool.starmap_async(
                        processWithoutTime, [(func, args, queue) for args in argsList])
                    pool.close()
                    for i in range(length):
                        sendStatusFunc(fileTime, msg, i, length)
                        queue.get()
                    sendStatusFunc(fileTime, msg, length, length)
                    return results.get()

__all__ = ["nullSendStatus", "multiProcess"]