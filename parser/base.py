from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T", bound=dict)

class BaseNode(ABC, Generic[T]):
    def __init__(self, verbose=False, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose

    @abstractmethod
    def run(self, state: T) -> T:
        pass

    def log(self, message: str, **kwargs):
        if self.verbose:
            print(f"[{self.name}] {message}")
            for key, value in kwargs.items():
                print(f"  {key}: {value}")

    def __call__(self, state: T) -> T:
        return self.run(state)