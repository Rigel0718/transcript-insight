from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import time

T = TypeVar("T", bound=dict)

class BaseNode(ABC, Generic[T]):
    def __init__(self, verbose=False, track_time=False, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose
        self.track_time = track_time

    @abstractmethod
    def run(self, state: T) -> T:
        pass

    def log(self, message: str, **kwargs):
        if self.verbose:
            print(f"[{self.name}] {message}")
            for key, value in kwargs.items():
                print(f"  {key}: {value}")

    def __call__(self, state: T) -> T:
        if self.track_time:
            start = time.time()
            result = self.run(state)
            duration = time.time() - start
            self.log(f" Finished in {duration:.2f} second")
            return result
        else :
            return self.run(state)