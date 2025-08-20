from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import time
from queue import Queue

T = TypeVar("T", bound=dict)

class BaseNode(ABC, Generic[T]):
    def __init__(self, verbose=False, track_time=False, queue: Queue=None, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose
        self.track_time = track_time
        self.queue = queue

    @abstractmethod
    def run(self, state: T) -> T:
        pass

    def log(self, message: str, **kwargs):
        if not self.verbose:
            return
        print(f"[{self.name}] {message}")
        for key, value in kwargs.items():
            print(f"  {key}: {value}")

    def emit_event(self, status: str, **extras):
        if self.queue:
            self.queue.put({
                'name': self.name,
                'status': status,
                **extras
            })

    def __call__(self, state: T) -> T:
        self.emit_event("start")
        
        if self.track_time:
            self.log(f"====< START >====")
            start = time.time()

        result = self.run(state)
        
        if self.track_time:
            duration = time.time() - start
            self.log(f" Finished in {duration:.2f} second")
            self.log(f"====< END >====")
            self.emit_event("end", duration=f"{duration:.2f}")
        else:
            self.emit_event("end")

        return result