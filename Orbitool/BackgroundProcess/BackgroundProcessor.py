from types import MethodType
from multiprocessing import Process, Queue
from enum import Enum

from functools import partial
import time

time.sleep(2)

class Processor:
    def __init__(self):
        self.a = 0

    def set_a(self, a):
        self.a = a
    
    def get_a(self):
        time.sleep(2)
        return self.a

    def routine(self, call, ret):
        while True:
            cal = call.get()
            attr, args, kwargs = cal
            print(f'recv {attr}')
            if attr == 'quit':
                print('return')
                ret.put(None)
                return
            ret.put(getattr(self, attr)(*args, **kwargs))
