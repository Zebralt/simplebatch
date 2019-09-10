
import threading
from contextlib import contextmanager


"""
Wrap an object with a 'lock' mechanism between threads
"""


class Locker:

    def __init__(self, target):
        self._target = target
        self.owner = None

    def acquire(self):
        self.owner = threading.get_ident()

    @property
    def target(self):
        while self.locked and threading.get_ident() != self.owner:
            pass
        return self._target

    @property
    def locked(self):
        return self.owner is not None

    def release(self):
        self.owner = None

    @contextmanager
    def lock(self):
        self.acquire()
        yield
        self.release()


if __name__ == "__main__":
    
    a = object()
    a = Locker(a)

    with a.lock():
        print(a.target)
        print(a.owner)