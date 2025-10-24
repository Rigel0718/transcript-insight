from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import time
from queue import Queue
from logging import LoggerAdapter
import logging
from typing import Optional
from app.core.env_model import Env
from app.core.logger import NoopRunLogger



T = TypeVar("T", bound=dict)

class BaseNode(ABC, Generic[T]):
    def __init__(self, env: Env, verbose=False, track_time=False, queue: Queue=None, logger: Optional[LoggerAdapter] = None, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose
        self.track_time = track_time
        self.queue = queue
        self.env = env
        self.run_logger = getattr(env, "run_logger", None)
        self.logger: LoggerAdapter | None = logger

    @abstractmethod
    def run(self, state: T) -> T:
        pass
    
    def _setup_logger(self, state: T):
        """self.logger가 항상 LoggerAdapter가 되도록 설정한다.
        - 주입(logger 파라미터)이 있으면 그대로 사용
        - 없으면 env.run_logger.get_logger(...) 또는 Noop로 대체
        - run_id가 없으면 NoopRunLogger로 일관화
        """

        if isinstance(self.logger, LoggerAdapter):
            return

        run_id = None
        try:
            run_id = state.get("run_id")
        except Exception:
            run_id = None
        
        node_name = getattr(self, "name", self.__class__.__name__)
        work_dir = getattr(self.env, "work_dir", ".")
        user_id = getattr(self.env, "user_id", "anonymous")

        if not run_id:
            # run_id = '-'로 일관화
            self.logger = NoopRunLogger().get_logger(work_dir, user_id, "-", node_name)
            return

        run_logger = getattr(self.env, "run_logger", None) or NoopRunLogger()
        self.logger = run_logger.get_logger(work_dir, user_id, run_id, node_name)

    def log(self, message: str, level: int = logging.INFO, **kwargs):
        logger = self.logger

        if not isinstance(logger, LoggerAdapter):
            logger = NoopLoggerAdapter()
            self.logger = logger
        extras_from_user = kwargs.pop("extra", {})
        extra = {**extras_from_user, **kwargs}
        logger.log(level, message, extra=extra)

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
