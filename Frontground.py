from functools import partial

class Redirector:
    def __init__(self,call,ret):
        print('inited')
        self.__call = call
        self.__return = ret

    def __getattr__(self, attr):
        return partial(self.__put, attr = attr)

    def __put(self, attr, *args, **kwargs):
        self.__call.put((attr, args, kwargs))
        return self.__return.get()
