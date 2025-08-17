from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import time
from queue import Queue
from logging import LoggerAdapter

T = TypeVar("T", bound=dict)

class BaseNode(ABC, Generic[T]):
    def __init__(self, verbose=False, track_time=False, queue: Queue=None, run_logger=None, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose
        self.track_time = track_time
        self.queue = queue
        self.run_logger = run_logger
        self.logger: Optional[LoggerAdapter] = None

    @abstractmethod
    def run(self, state: T) -> T:
        pass
    
    def _ensure_logger(self, state: T):
        if self.logger is not None:
            return
        if self.run_logger is None:
            base = logging.getLogger(self.name)
            self.logger = logging.LoggerAdapter(base, {"component": self.name})
            return
        base_logger = self.run_logger.configure_logger(state, component=self.name)
        self.logger = logging.LoggerAdapter(base_logger, {"component": self.name})


    def log(self, message: str, level: int = logging.INFO, **kwargs):
        if self.logger is None:
            base = logging.getLogger(self.name)
            self.logger = logging.LoggerAdapter(base, {"component": self.name})
        self.logger.log(level, message, extra={"component": self.name, **kwargs})

    def emit_event(self, status: str, **extras):
        if self.queue:
            self.queue.put({
                'name': self.name,
                'status': status,
                **extras
            })

    def __call__(self, state: T) -> T:
        self._ensure_logger(state)
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