from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import time
from queue import Queue
from logging import LoggerAdapter
import logging
from typing import Optional
from base_node.env_model import Env




T = TypeVar("T", bound=dict)

class BaseNode(ABC, Generic[T]):
    def __init__(self, env: Env, verbose=False, track_time=False, queue: Queue=None, logger: Optional[LoggerAdapter] = None, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose
        self.track_time = track_time
        self.queue = queue
        self.env = env
        self.run_logger = logger or env.run_logger
        self.logger: Optional[LoggerAdapter] = None

    @abstractmethod
    def run(self, state: T) -> T:
        pass
    
    def _setup_logger(self, state: T):
        if self.logger is not None:
            return
        if self.run_logger:
            self.logger = self.run_logger.get_logger(
                work_dir=self.env.work_dir,
                user_id=self.env.user_id,
                run_id=state['run_id'],
                node_name=self.name
            )


    def log(self, message: str, level: int = logging.INFO, **kwargs):
        if self.logger is None:
            self._setup_logger({})
        self.logger.log(level, message, extra={"node_name": self.name, **kwargs})

    def emit_event(self, status: str, **extras):
        if self.queue:
            self.queue.put({
                'name': self.name,
                'status': status,
                **extras
            })

    def __call__(self, state: T) -> T:
        self._setup_logger(state)
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